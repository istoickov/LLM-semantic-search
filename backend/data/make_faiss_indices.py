"""
This script is used to generate the faiss indices for the embeddings generated by the models.
"""

from pprint import pprint

import json
import os
import numpy as np


from process import Process
from backend.utils import data_utils

DEBUG = False

data_utils_obj = data_utils.DataUtils()
process_obj = Process()


def print_output(indices, original_data, model_name, query, option=None):
    """Prints the output of the query.

    Args:
        indices (_type_): _description_
        original_data (_type_): _description_
        model_name (_type_): _description_
        query (_type_): _description_
        option (_type_, optional): _description_. Defaults to None.
    """
    print("-" * 70)
    print("-" * 70)
    print(f"Query: {query}")
    print(f"Model: {model_name}")
    print(f"Option: {option}")
    for index in indices[0]:
        item = original_data[index]
        pprint(
            {
                "name": item["name"],
                "country": item["state"],
                "full_name": item.get("instagram", {}).get("full_name"),
                "bio": item.get("instagram", {}).get("bio"),
                "follows": item.get("instagram", {}).get("follows"),
                "following": item.get("instagram", {}).get("following"),
                "tags": item.get("tags", []),
            }
        )
        print("-" * 50)
    print("-" * 70)
    print("-" * 70)


def run(query_list):
    """Runs the script

    Args:
        query_list (List[str]): List of queries to run the script on.
    """
    data = json.load(open("./data/_model_data.json", "r", encoding="utf-8"))

    text_summaries = data_utils_obj.make_summaries(data)
    text_summaries = data_utils_obj.clean_summaries(text_summaries)

    for option in range(0, 6):
        print(f"Option: {option}")
        try:
            cleaned_text_summaries = process_obj.load_data(f"./data/data_{option}.json")
        except FileNotFoundError as e:
            print(f"Exception: {e}")
            cleaned_text_summaries = None

        if cleaned_text_summaries is None:
            cleaned_text_summaries = text_summaries

            if option == 1:
                cleaned_text_summaries = data_utils_obj.lemmatization_data(
                    text_summaries
                )
            elif option == 2:
                cleaned_text_summaries = data_utils_obj.stemm_data(text_summaries)
            elif option == 3:
                cleaned_text_summaries = data_utils_obj.remove_stopwords(text_summaries)
            elif option == 4:
                cleaned_text_summaries = data_utils_obj.remove_stopwords(text_summaries)
                cleaned_text_summaries = data_utils_obj.stemm_data(text_summaries)
            elif option == 5:
                cleaned_text_summaries = data_utils_obj.remove_stopwords(text_summaries)
                cleaned_text_summaries = data_utils_obj.lemmatization_data(
                    text_summaries
                )

            process_obj.save_data(cleaned_text_summaries, f"./data/data_{option}.json")

        for model_name in process_obj.ml_utils:
            print(f"Model: {model_name}")

            embeddings_path = f"./data/{option}_{model_name}_embeddings.npy"
            if os.path.exists(embeddings_path):
                # Load embeddings from the file
                embeddings = np.load(embeddings_path)
            else:
                # Generate embeddings
                embeddings = process_obj.make_embeddings(
                    cleaned_text_summaries, model_name
                )
                # Save the new embeddings to a file
                np.save(embeddings_path, embeddings)
                print("Embeddings shape: ", embeddings.shape)

            if os.path.exists(f"./data/{option}_{model_name}.faiss"):
                index = process_obj.faiss_client.retrive_index(
                    f"./data/faiss_index_{option}_{model_name}.faiss"
                )
            else:
                index = process_obj.make_faiss_index(
                    embeddings, f"{option}_{model_name}"
                )

            for query in query_list:
                print(f"Query: {query}")
                query = data_utils_obj.clean_summary(query)

                if option == 1:
                    query = data_utils_obj.lemmatization_senetence(query)
                elif option == 2:
                    query = data_utils_obj.stemm_sentence(query)
                elif option == 3:
                    query = data_utils_obj.remove_stopwords(query)
                elif option == 4:
                    query = data_utils_obj.remove_stopwords([query])
                    query = data_utils_obj.stemm_sentence(query[0])
                elif option == 5:
                    query = data_utils_obj.remove_stopwords([query])
                    query = data_utils_obj.lemmatization_senetence(query[0])

                query_embeddings = process_obj.get_query_embeddings(query, model_name)

                print("Query embedding shape: ", query_embeddings.shape)
                distances, indices = index.search(query_embeddings, 10)
                print("Distances: ", distances)
                print("Indices: ", indices)

                print_output(indices.tolist(), data, model_name, query, option)


if __name__ == "__main__":
    process_obj = Process()

    queries = [
        "Girl influencers based in the Germany",
        "Fashion influencers based in the America",
        "Skin care influencers based in the United Kingdom",
        "Animal activists based in UK",
        "e-Sports people from USA",
    ]
    config = [
        {
            "model": "sbert_short",
            "model_name": "SBERT_short",
        },
        {
            "model": "sbert",
            "model_name": "SBERT",
        },
        {
            "model": "minilm",
            "model_name": "MiniLM",
        },
        {
            "model": "roberta",
            "model_name": "RoBERTa",
        },
        {
            "model": "bert",
            "model_name": "BERT",
        },
    ]

    run(queries)
