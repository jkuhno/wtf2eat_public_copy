import { useNavigate, Link } from "react-router-dom";


const HomePage = () => {

    const navigate = useNavigate();

    const handleGoLogin = () => {
        navigate("/login");
    };

    const handleGoRegister = () => {
        navigate("/register");
    };

    return (
        <div>
         <h1>What the f*** to eat?</h1>
         <p> Restaurant recommendations formulated with nerdy maths. <br/>
         Free to use but you might experience 
         <a href="https://developer.mozilla.org/en-US/docs/Glossary/Rate_limit" 
                                 target="_blank" 
                                 rel="noopener noreferrer"> rate limits. </a></p>
         <button className="reroll-button" onClick={handleGoLogin}>
             Sign in 🔑
          </button>
          <button className="reroll-button" onClick={handleGoRegister}>
            Register 📝
          </button>
          <div className="contact-button">
                <p><Link to="/contact">Contact</Link></p>
          </div>
          <div className="info-header">
                <h2>Why</h2>
                <p>Sometimes we get indecisive about food. <br/> In that situation it really helps 
                to have someone give you three options to choose from. <br/> 
                On top of that, the suggestions are better if that someone knows what you like. <br/> 
                But we don't want to hire a person to do that. That's why we need a robot.<br/> 
                </p>
          </div>
        </div>
    );
    };

export default HomePage;