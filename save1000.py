from neo4j import GraphDatabase
import json
def sendToNeo4j(query, **kwargs):
    driver = GraphDatabase.driver('bolt://167.71.99.31:7687', auth=('neo4j', 'graph'))
    db = driver.session()
    consumer = db.run(query, **kwargs) 
    print('done')
    
with open('covid_obj.json', 'r') as f:
    documents = json.load(f)



query = """with $documents as rows
unwind rows as row
with row.object as graph_obj, row
unwind keys(graph_obj) as obj_key 
with graph_obj[obj_key] as graphs, obj_key, row
UNWIND range(0,size(graphs)-2) as idx 
MERGE (abstract:ABSTRACT {text:row.abstract})
MERGE (abstract)<-[sf:SENTENCE_FROM {text:apoc.text.join(graphs[idx]['noun_phrase'] + graphs[idx]["noun_connectors"] + graphs[idx + 1]['noun_phrase'], " ")}]-(s:Facts {text:obj_key})
"""
sendToNeo4j(query, documents=documents) 


query1 = """
with $documents as rows
unwind rows as row
unwind row.authors as authors


MERGE (paper:Paper {text:row['url']})
MERGE (paper)-[:PAPER_SOURCE]->(source:SOURCE {text:row.site})
merge (title:Title {text:row.title})
merge (abstract:ABSTRACT {text:row.abstract})
merge (author:AUTHOR {author_name: authors.author_name, author_institution: authors.author_inst })
merge (publish_date:PUBLISH_DATE {text:row.publication_date})
merge (paper)-[:PAPER_TITLE]->(title)
MERGE (paper)-[:ABSTRACT]->(abstract)
MERGE (paper)-[:AUTHOR]->(author)
MERGE (paper)-[:PUBLISH_DATE]->(publish_date)

//return tag
"""
sendToNeo4j(query1, documents=documents) 


