  
#Copyright (c) Microsoft Corporation. All rights reserved.
#Licensed under the MIT License.

# -*- coding: utf-8 -*-

import json
import os 
from pprint import pprint
import requests


from bs4 import BeautifulSoup as bs
from urllib.request import urlopen, Request
from nltk.tokenize import sent_tokenize

import spacy
nlp = spacy.load('en_core_web_sm')
from neo4j import GraphDatabase


import pandas as pd
import numpy as np
import os

def sendToNeo4j(query, **kwargs):
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'graph'))
    db = driver.session()
    consumer = db.run(query, **kwargs) 
    print('done')

# Add your Bing Search V7 subscription key and endpoint to your environment variables.

subscription_key  = "66de9acf13be4e1f96aafef3cdcfc2e5"

# Construct a request
headers = { 'Ocp-Apim-Subscription-Key': subscription_key }
customconfig = "59e8892a-85af-4b70-a2d0-9746290dd65e"
def search_web(search_query):
    endpoint =  'https://api.cognitive.microsoft.com/bingcustomsearch/v7.0/search?' + 'q=' + search_query + '&' + 'customconfig=' + customconfig

# Call the API

    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        json_response = response.json()
        json_response_array = json_response["webPages"]['value']

        for i in json_response_array[:3]:

            request = requests.get(i['url'])
            
            if request.status_code == 200:
                link = i['url']
                soup = bs(request.text, 'html.parser')
                find_h1 = soup.find('h1')
                if find_h1:
                    title = find_h1.get_text(strip=True)
                p_container = soup.find_all('p')
                articles = ""
                for p_tag in p_container:
                    if len(p_tag.get_text(strip=True)) > 15:
                        articles += ''.join(p_tag.get_text(strip=True))
                meta_tag = soup.find('meta', {"property":"og:description"})
                meta_tag_content = ""
                if soup.find('meta', {"property":"og:description"}):
                    meta_tag_content = meta_tag['content']
             
                if len(articles):
                    full_documnent = articles + meta_tag_content
                    sent_token = sent_tokenize(full_documnent)
#                    MODEL_NAME = 'sentimentdl_use_twitter'
#                    documentAssembler = DocumentAssembler().setInputCol("text").setOutputCol("document")
#
#                    tokenizer = Tokenizer() \
#                    .setInputCols(["document"]) \
#                    .setOutputCol("token")
#
#                    pos = PerceptronModel.pretrained("pos_anc", 'en')\
#                            .setInputCols("document", "token")\
#                            .setOutputCol("pos")
#
#                    dep_parser = DependencyParserModel.pretrained('dependency_conllu')\
#                            .setInputCols(["document", "pos", "token"])\
#                            .setOutputCol("dependency")
#
#
#                    typed_dep_parser = TypedDependencyParserModel.pretrained('dependency_typed_conllu')\
#                            .setInputCols(["token", "pos", "dependency"])\
#                            .setOutputCol("dependency_type")
#
                    # use = UniversalSentenceEncoder.pretrained(name="tfhub_use", lang="en")\
                    #         .setInputCols(["document"])\
                    #         .setOutputCol("sentence_embeddings")
                            
                    # sentimentdl = SentimentDLModel.pretrained(name=MODEL_NAME, lang="en")\
                    #         .setInputCols(["sentence_embeddings"])\
                    #         .setOutputCol("sentiment")
                    
#                    nlpPipeline = Pipeline(
#                        stages = [
#                            # sentence_detector
#                            # documentAssembler
#                            documentAssembler,
#                            tokenizer,
#                            pos,
#                            # chunker,
#                            dep_parser,
#                            typed_dep_parser,
#                            # use,
#                            # sentimentdl
#                        ])
                    # index=0
#                    empty_df = spark.createDataFrame([['']]).toDF("text")
#                    pipelineModel = nlpPipeline.fit(empty_df)
#                    print(sent_token)
#                    df = spark.createDataFrame(pd.DataFrame({"text":sent_token[0:3]}))
#                    result = pipelineModel.transform(df)
                    # print(result.keys())
#                    resut = result.toPandas()
                    # resut = result.select(F.explode(F.arrays_zip('token.result',
                    #                  'token.begin',
                    #                  'token.end', 
                    #                  'pos.result', 
                    #                  'dependency.result', 
                    #                               'dependency.metadata',
                    #                               'dependency_type.result')).alias("cols"))\
                    #                               .select(F.expr("cols['0']").alias("chunk"),
                    #                                       F.expr("cols['1']").alias("begin"),
                    #                                       F.expr("cols['2']").alias("end"),
                    #                                       F.expr("cols['3']").alias("pos"),
                    #                                       F.expr("cols['4']").alias("dependency"),
                    #                                       F.expr("cols['5']").alias("dependency_start"),
                    #                                       F.expr("cols['6']").alias("dependency_type")).toPandas()
#                    resut.to_csv('re.csv')
#
#                    print(resut)
                    
                    # sent_token = sent_tokenize(full_documnent)
                    counts = {}
                    for sentence in sent_token:
                        if sentence not in counts:
                            counts[sentence] = 0

                        counts[sentence] += 1
                    article = ""
                    # print(counts)
                    final_tag = dict()
                    for k, v in counts.items():
                        # print(k)
                        if v == 1:
                            # print(k)
                            article += ''.join(k)
                            total_graphObj = []
                            graph_obj = {
                                "noun_phrase": "",
                                "noun_connectors": []
                            }
                            total_word_token = [(tok.text, tok.pos_) for tok in nlp(k)]
                            # print(total_word_token)
                            for index, word_token in enumerate(total_word_token):
                                if(word_token[1] == "PUNCT"):
                                    continue
                                if((word_token[1] == "NOUN" or word_token[1] == "PROPN" or word_token[1] == 'ADJ') and len(graph_obj["noun_connectors"]) == 0):
                                    graph_obj["noun_phrase"] += f" {word_token[0]}"
                            
                                elif(word_token[1] == "NOUN" and len(graph_obj["noun_connectors"]) > 0):
                                    total_graphObj.append(graph_obj)
                                    graph_obj = {
                                    "noun_phrase": "",
                                    "noun_connectors": []
                                    }
                                    graph_obj["noun_phrase"] += f" {word_token[0]}"
                                 
                                elif word_token[1] == "VERB" or word_token[1] == "ADV" or word_token[1] == "ADV" or word_token[1] == "CCONJ":
                                    graph_obj["noun_connectors"].append(word_token[0])
                                if((index + 1) == len(total_word_token)):
                                    total_graphObj.append(graph_obj)
                            final_tag.update({k : total_graphObj})
                    sentence_total_graphObj  = {"title":title, "article" : article, "object":final_tag, 'link':link}
                    # print(sentence_total_graphObj)       
                    query = """
                    with $sentence_total_graphObj as row
                    with row.object as graph_obj, row
                    unwind keys(graph_obj) as obj_key
                    with graph_obj[obj_key] as graphs, obj_key, row, graph_obj
                    UNWIND range(0,size(graphs)-2) as idx 
                    MERGE (title: Title {text:row.title, source:"source", links:"links", type:"STRING"})
                    MERGE (article:ARTICLE {text: row.article, source:"source", links:"links", type:"STRING"})
                    MERGE (title)<-[:PAPER_TITLE]-(article)
                    MERGE (article)<-[sf:SENTENCE_FROM {text:apoc.text.join(graphs[idx]['noun_phrase'] + graphs[idx]["noun_connectors"] + graphs[idx + 1]['noun_phrase'], " ")}]-(s:Results {text:obj_key, source:"ARTICLE", links:row.link, type:"STRING"})
                    with row
                    MATCH (n) SET n.index = id(n)
                    with labels(n) as label, n
                    SET n.category = label[0]
                    //match(n)
                    //with apoc.meta.types(n) as dtypes, n
                    //set n.type = dtypes.text
                    //return dtypes.text
                     """       
                    # sendToNeo4j(query, sentence_total_graphObj=sentence_total_graphObj)
                    
                    
                    
                    


    except Exception as ex:
        raise ex
search_query = "effect of covid"    
search_web(search_query)
