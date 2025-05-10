from langgraph.graph import START, END, MessagesState, StateGraph # type: ignore
from langchain_core.messages import HumanMessage, SystemMessage # type: ignore
from langchain_core.runnables.config import RunnableConfig # type: ignore
from langgraph.types import StreamWriter # type: ignore

import re
import uuid

from models.llm import get_chat_model
from utils.db_client import ConnectPostgres 
from utils.maps import get_restaurants
from utils.graph_utils import check_preference_negative, check_preference_score, remove_duplicates

# Custom state for the graph
# Enables future manipulation
class State(MessagesState):
    input: str
    decision: str
    query: str
    output: list
    restaurants: list
    state_token_count: int

def get_graph(db: ConnectPostgres):
    
    router_llm = get_chat_model('deepseek-r1-distill-llama-70b', temperature=0)
    query_llm = get_chat_model('gemma2-9b-it', temperature=0)


    # A small model cant handle the decision when making a tool call
    # Currently using a model that does reasoning with <think> tags, prefer that
    def router_model(state: State, writer: StreamWriter):
        '''Used to decide if user input contains
           pereferences that need to be saved'''
        
        input = state["input"]
    
        sys_prompt ='''You are a router tasked to output a route that best matches the following use cases.
    "no" is a route used for time when user requests something, but does not implicate a preference that could be saved. 
    This route is also the default route.
    "save" is a route used when user both requests something, and it is a preference or remark that should be saved.
    "end" is a route used when user presents a preference or remark, but does not request any help 
    with decision or restaurant recommendations.
    '''
    
        human_msg = f'''Decide a route for this input: {input}. Output in JSON format: {{"route": **your answer**}}.
    Do not output anything else.'''
        

        msg = [SystemMessage(content=sys_prompt),
               HumanMessage(content = human_msg)]
        
        writer({"custom_key": "Deciding a route"})

        ans = router_llm.invoke(msg)
    
        # Check if llm answer contains thinking tags
        # Hopefully it does, but needs to be parsed for the conditional to match properly
        match = re.search(r"</think>\s*(.*)", ans.content, re.DOTALL)
        result = match.group(1) if match else ans.content
        
        # Should result in {"router": **answer**}
        return {"decision": result, "state_token_count": ans.usage_metadata["total_tokens"]}


    def router_conditional(state: State, config: RunnableConfig):
        router_answer = state["decision"]
    
        if "save" in router_answer:
            print(f"Saved: {state['input']}")
            return 'save'
        elif "end" in router_answer:
            print(f"Exiting, saving manually: {state['input']}")
            save_preference(state, config)
            return 'save_and_end'
        else:
            print(f"Did not save: {state['input']}")
            return 'no_save'
    

    def save_preference(state: State, config: RunnableConfig):
        ''' Use this function to save user preferences '''

        user_id = config["configurable"]["user_id"]
        
        with db.get_store() as store:
            store.put(("users", user_id), 
                        uuid.uuid4(), 
                        {
                         "preference": state['input'], 
                        },
                        index=["preference"])


    # Makes the query from a sometimes vague user input
    def query_formulator(state: State, writer: StreamWriter):
        global global_token_count
        sys_prompt = f"""
        You are a diligent restaurant recommendation query formatter.
        
        Formulate a query string from the user input, that when used as a query to search for restaurants, 
        produces results that satisfy the user intent.
        
        The query must describe the types of restaurants.
        Use 1-4 words only.
        
        Refrain from using location information in the query, like terms 'near me' or 'in Helsinki'.
        Output only the query, no additional explanation is needed.
        """
    
        writer({"custom_key": "Generating a query"})

        input = state["input"]
        
        sys = SystemMessage(sys_prompt)
        usr = HumanMessage(input)
    
        answer = query_llm.invoke([sys, usr])

        tokens = state["state_token_count"]
        tokens += answer.usage_metadata["total_tokens"]
    
        return {"query": answer.content, "state_token_count": tokens}
    

    def get_restaurant_list(state: State, config: RunnableConfig, writer: StreamWriter):
        '''Get a list of restaurants from Google Maps
        LLM NOT USED
        get_restaurants is a function for the actual API query, stores results in vector db (to save money)
        TODO: room for more logic
        '''
        query = state["query"]

        writer({"custom_key": "Searching for restaurants"})

        location: dict = config["configurable"]["location"]
    
        # gets a list of dicts containing Google Maps results, keys "name" and "reviews"
        hits = get_restaurants(query, db, location)
    
        hits = remove_duplicates(hits)
    
        return {"restaurants": hits}


    def preference_checker(state: State, config: RunnableConfig, writer: StreamWriter):
        '''Add information about preferences to the restaurant list
        Vector search for selecting which preferences should increase the value of the restaurant.
        A stupid function is used for selecting non-preferred restaurants
        with a list of negative words and fuzzywuzzy matching score.
        Outputs a list of restaurants added with "pref_note" key
        '''
        
        restaurant_list = state["restaurants"]
        user_id = config["configurable"]["user_id"]

        writer({"custom_key": "Calculating user preferences"})

        with db.get_store() as store:
            user_preferences = store.search(("users", user_id))
    
    
        # Go through every user preference. If a preference is found that forbids use, that restaurant gets a 'pop'
        # in the state
        # If no forbiddings are found, a restaurant gets either 'boost' or 'none' tag in state
        
        # elements get 'boost' note here if strong match with preferences, either 'none'
        restaurant_list = check_preference_score(restaurant_list, user_id, user_preferences, db)
    
        # restaurant: {"name": Restaurant Name, "reviews": ["Review 1: abcd, Review 2: xyzd"]}
        for restaurant in restaurant_list:
               
                for pref in user_preferences:
                    neg = check_preference_negative(restaurant['name'], pref.value['preference'])
                    if neg == 'pop':
                        restaurant["pref_note"] = 'pop'

                
        return {'restaurants': restaurant_list}


    def sort_restaurants(state: State, config: RunnableConfig, writer: StreamWriter):
        '''Sort the restaurants according to the similarity score between reviews and original request by user
        Add preference information by decreasing score of preferred and increasing non-preferred 
        (smaller is better)
        LLM NOT USED
        Outputs a sorted list of restaurant Documents, first (lowest score) is best
        '''
        raw_result = state["restaurants"]
        user_id = config["configurable"]["user_id"]
        input = state["input"] 
    
        writer({"custom_key": "Ranking the restaurants"})
        

        # reviews already indexed in previous step
        for restaurant in raw_result:
            with db.get_store() as store:
                store.put(namespace=("rank_restaurants", user_id), 
                          key=restaurant["name"], 
                          value={
                           "pref_note": restaurant["pref_note"]
                          }
                )
                

        # score_item:
        # Item(namespace=['rank_restaurants', '1'], 
        #      key='Rice Story', 
        #      value={'reviews': ['Review 1: Service was fast and friendly, '], 'pref_note': 'none'},
        #      created_at='2025-03-16T18:42:23.348161+00:00', updated_at='2025-03-16T18:42:23.348161+00:00', 
        #      score=0.35495079621526004)
        with db.get_store() as store:
            score_items = store.search(("rank_restaurants", user_id), query=input, limit=9)


        # Delete, needs a way to filter rather than delete to save embeddings calls
        for restaurant in raw_result:
            with db.get_store() as store:
                store.delete(namespace=("rank_restaurants", user_id), 
                             key=restaurant["name"]
                )

        
        # ('iizip Korean Restaurant (iizip & BBQ)', 0.5731853032112122)
        updated_tuple_list = []
        for i in score_items:
            name = i.key 
            score = i.score

            match = next((item for item in raw_result if item["name"] == name), None)
    
            if match:
                rating = match["rating"]
                delivery = match["delivery"]
                maps_uri = match["maps_uri"]
                photo = match["photo"]

            # using cosine similarity, check for the need to add or subtract based on the metric
            if i.value["pref_note"] == "boost":
                score += 0.04 
            if i.value["pref_note"] == "pop":
                score -= 0.06
            updated_tuple_list.append((name, score, rating, delivery, maps_uri, photo))
    
        # reverse means ascending, based on the similarity metric
        sorted_tuple_list = sorted(updated_tuple_list, key=lambda x: x[1], reverse=True)

        return {'output': sorted_tuple_list}
    
    workflow = StateGraph(State)

    # Define the two nodes we will cycle between
    workflow.add_node("router_LLM", router_model)
    workflow.add_node("saver_FUNC", save_preference)
    workflow.add_node("query_LLM", query_formulator)
    workflow.add_node("restaurants_FUNC", get_restaurant_list)
    workflow.add_node("preferences_FUNC", preference_checker)
    workflow.add_node("sort_FUNC", sort_restaurants)
    
    workflow.add_edge(START, "router_LLM")
    workflow.add_conditional_edges("router_LLM", 
                                   router_conditional, 
                                   {
                                       "save": "saver_FUNC",
                                       "no_save": "query_LLM",
                                       "save_and_end": END
                                   })
    
    workflow.add_edge("saver_FUNC", "query_LLM")
    workflow.add_edge("query_LLM", "restaurants_FUNC")
    workflow.add_edge("restaurants_FUNC", "preferences_FUNC")
    workflow.add_edge("preferences_FUNC", "sort_FUNC")
    workflow.add_edge("sort_FUNC", END)
    
    #checkpointer = MemorySaver()
    app = workflow.compile()
    app.name = "gmaps_graph"

    return app
