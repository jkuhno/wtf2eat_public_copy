from langgraph.store.postgres import PostgresStore # type: ignore
import os


class ConnectPostgres:
    def __init__(self, embeddings, dims):
        user = os.environ['POSTGRES_USER']
        pw = os.environ['POSTGRES_PASSWORD']
        host = os.environ['POSTGRES_HOST']

        connection_string=f"postgresql://{user}:{pw}@{host}:5432/postgres"

        self.connection_string = connection_string
        self.embeddings = embeddings
        self.dims = dims
        self.user = user
        self.pw = pw


    def get_store(self):
        """
        Create and return a PostgresStore instance.

        Returns:
            PostgresStore: Configured PostgresStore instance.
        """
        return PostgresStore.from_conn_string(
            self.connection_string,
            index={
                "dims": self.dims,
                "embed": self.embeddings,
                "distance_type": "cosine"
                 # distance_type: Literal["l2", "inner_product", "cosine"]
                  # Distance metric to use for vector similarity search:
                  # 'l2': Euclidean distance
                  # 'inner_product': Dot product
                  # 'cosine': Cosine similarity
                  # 
            },
        )