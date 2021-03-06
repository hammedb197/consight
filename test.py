from flask import Flask, request, render_template , flash, jsonify,redirect, url_for
from neo4j import GraphDatabase
import json
from werkzeug.utils import secure_filename

from bing_search import search_web




app = Flask(__name__, static_url_path='/static')
app.secret_key = 'dljsaklqk24e21cjn!Ew@@dsa5'
def sendToNeo4j(query, **kwarg):
    
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'graph'))
    db = driver.session()
    consumer = db.run(query, **kwarg) 
    return [dict(i) for i in consumer]

def sendToNeo4jsave(query, **kwargs):
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'graph'))
    db = driver.session()
    consumer = db.run(query, **kwargs)
    print('done')
    


"""SparkOcr.ipynb
Spark OCR

## Spark OCR transformers and Spark NLP annotators
"""

secret = "1.5.0-c4b7ea9d20fe45e4c9583706861ab246300d3339"
license = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJleHAiOjE1OTkxNTczNTIsImlhdCI6MTU5NjU2NTM1MiwidW5pcXVlX2lkIjoiNzY2YWJkZTItZDY3Zi0xMWVhLWIyZmQtNDI4NTYwZmE4NjZhIn0.BMj_VBfKvSqu74qUbArIWEHNnO-ePDZkyBZDrtOhDdLgDZAQoPEKrH4sqo6bPER5lks4ykKw59xI2EpToPb5fQ_Ydyc8eNYBdpieDTctYOIFLEy3ne4TCVy8IJsaOqsYtVI9aWWav6rjBUkFv_cJkhfyGqG36s40gALo6WNHMJXSrEpHrTY-qQctrX-Hiy242CiVDs3ZTTSfVfyH5SXI371G0TOVSG7BNWR3ZQ0gSb7BnQpoPVblYEnkqgKxl-OUP15hLGHguWKyfYtMvqCyQIdA0ewr0OpaFwS4n_QHx95xNyCV2Ozs0NcyOePTq1I9187gIk386NdJkyngx4Iz1g"
version = secret.split("-")[0]
spark_ocr_jar_path = "../../target/scala-2.11"


import os
import sys


"""## Initialization of spark session
Need specify path to `spark-ocr-assembly.jar` or `secret`
"""
 os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-8-openjdk-amd64/jre"
#os.environ['JAVA_HOME'] = "/Library/Java/JavaVirtualMachines/jdk1.8.0_231.jdk/Contents/Home/jre"
from sparkocr import start


if license:
    os.environ['JSL_OCR_LICENSE'] = license

spark = start(secret=secret, nlp_version="2.4.5")


from pyspark.ml import Pipeline
from pyspark.ml import PipelineModel
from sparkocr.transformers import *
from sparknlp.annotator import *
from sparknlp.base import *
from sparkocr.enums import PageSegmentationMode

"""## Define OCR transformers and pipeline"""

def update_text_pipeline():

    document_assembler = DocumentAssembler() \
        .setInputCol("text") \
        .setOutputCol("document")

    sentence_detector = SentenceDetector() \
        .setInputCols(["document"]) \
        .setOutputCol("sentence")

    tokenizer = Tokenizer() \
        .setInputCols(["sentence"]) \
        .setOutputCol("tokens")

#    spell = NorvigSweetingModel().pretrained("spellcheck_norvig", "en") \
          .setInputCols("tokens") \
          .setOutputCol("spell")
    
#    tokenAssem = TokenAssembler() \
          .setInputCols("spell") \
          .setOutputCol("newDocs")

#    updatedText = UpdateTextPosition() \
          .setInputCol("positions") \
          .setOutputCol("output_positions") \
          .setInputText("newDocs.result")

    pipeline = Pipeline(stages=[
        document_assembler,
        sentence_detector,
        tokenizer,
#        spell,
#        tokenAssem,
#        updatedText
    ])
    
    return pipeline


def ocr_pipeline():
    # Transforrm PDF document to images per page
        pdf_to_image = PdfToImage() \
            .setInputCol("content") \
            .setOutputCol("image_raw") \
            .setKeepInput(True)

        # adaptive_thresholding = ImageAdaptiveThresholding() \
        #     .setInputCol("image_raw") \
        #     .setOutputCol("corrected_image") \
        #     .setBlockSize(35) \
        #     .setOffset(80)

        binarizer = ImageBinarizer() \
            .setInputCol("image_raw") \
            .setOutputCol("image") \
            .setThreshold(130)

        ocr = ImageToText() \
            .setInputCol("image") \
            .setOutputCol("text") \
            .setIgnoreResolution(False) \
            .setPageSegMode(PageSegmentationMode.SPARSE_TEXT) \
            .setConfidenceThreshold(60)

        pipeline = Pipeline(stages=[
            pdf_to_image,
            binarizer,
            ocr
        ])
        return pipeline

 
def run_spark_pipeline(files):
    df = spark.read \
            .format("binaryFile") \
            .load(files)
    """## Run OCR pipelines"""
    # print('file laoded
    ocr_result = ocr_pipeline().fit(df).transform(df)
    result= update_text_pipeline().fit(ocr_result).transform(ocr_result)
    print("pipeline loaded")
    res = result.toPandas()
    print("to pandas")
    results = res[["path", "pagenum", "confidence", "text"]]
    document = {
    "pagenum": "",
    "sentence": [],
    "content" : [],
    "documentnum" : '',
    "confidence": ""
    }
    for i in result["sentence"]:
        for sent in i:
          document['sentence'].append(sent["result"])
    for j in result['document']:
      document['content'].append(j[0]['result'])
    document['pagenum'] = list(result.pagenum)
    document['confidence'] = list(result.confidence)
    document["documentnum"] = list(result.documentnum)
    print(document)
    query = """
        with $document as row
        unwind row["pagenum"] as page_num
        unwind row["documentnum"] as document_num
        unwind row['confidence'] as confidence_level
        unwind row['content'] as doc_content
        unwind row.sentence as sent
        MERGE (pagnum:PAGE_NUMBER {text:page_num})
        MERGE (documentnum:DOCUMENT_NUMBER {text:document_num})
        MERGE (confidence: CONFIDENCE {text:confidence_level})
        MERGE (content:CONTENT {text:doc_content})
        MERGE (result: RESULT {text:sent})

        MERGE (documentnum)-[:PAGE_NUMBER]->(pagnum)
        MERGE (documentnum)-[:CONFIDENCE_LEVEL]->(confidence)
        MERGE (documentnum)-[:CONTENT]->(content)
        MERGE (documentnum)-[:SENTENCE]->(RESULT)

        """
    sendToNeo4jsave(query, document=document)
    return results

categor = []
graph_category  = []
def split_space(string):
    return " ".join(string.split("_")).capitalize()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search/', methods=["POST", "GET"])
def index_():
    if request.method == 'POST':
        text = request.form['text']
        if text == 'Covid-19':
            result_query = """
            CALL db.index.fulltext.queryRelationships("tags", $search_input) YIELD relationship, score
            where score > 1
            match (node)-[relationship]->(b)
            unwind labels(node) as n
            unwind labels(b) as bb
            //unwind nodes(path) as p, 
            with properties(node) as start, properties(b) as end

            with collect(distinct {startnode:start, endnode:end}) as result
            return result
            """
            result = sendToNeo4j(result_query, search_input=text)
        else:
            result_query = """
            CALL db.index.fulltext.queryRelationships("tags", $search_input) YIELD relationship, score
            where score > 1
            match (node)-[relationship]->(b)
            unwind labels(node) as n
            unwind labels(b) as bb
            //unwind nodes(path) as p, 
            with properties(node) as start, properties(b) as end
            with collect(distinct {startnode:start, endnode:end}) as result
            return result
            """
            result = sendToNeo4j(result_query, search_input=text)
            # print(result)
            # print(result[0]["result"])
            if len(result[0]["result"]) < 1 :
                search_web(text)
                result_query = """
                CALL db.index.fulltext.queryRelationships("tags", $search_input) YIELD relationship, score
                where score > 1
                match (node)-[relationship]->(b)
                unwind labels(node) as n
                unwind labels(b) as bb
                //unwind nodes(path) as p, 
                with properties(node) as start, properties(b) as end
                with collect(distinct {startnode:start, endnode:end}) as result
                return result
                """

                result = sendToNeo4j(result_query, search_input=text)
                # print(result)

                """
                get start node an endnote then extract category(unique) if len(str(j['startnode']['text'])) < 15
                """
                category_table = [j['startnode']['category'] + ":" + j["endnode"]['category'] for i in result for j in i['result'] if type(j['startnode']['text']) != list   if j['startnode']['text'] != "Unknown" if j['endnode']['text'] != "Unknown"]
                take_category = list(set(category_table))
        
                """
                object with category:text map
                """
                create_object = [{j['startnode']['category'] + ":" + j["endnode"]['category'] : str(j['startnode']['text']) + ":" + str(j["endnode"]['text'])} for i in result for j in i['result'] if "text" in j["endnode"] if "type" in j["endnode"] if type(j['startnode']['text']) != list ]
                
                """
                extract string integer map
                """
                string_integer = []
                for i in result:
                    for j in i['result']:
                        if "type" in j["endnode"]:
                            if j['startnode']['type'] == "STRING" and j['endnode']['type'] == "INTEGER":
                                string_integer.append({j["endnode"]['category'] : {"key" : j['startnode']['text'], "value":j["endnode"]['text']}})
                            # print({j["endnode"]['category'] : {j['startnode']['text']:j["endnode"]['text']}})
                      
                      
                """
                Category key:pair
                """
                category_key = []
                for h in string_integer:
                    for k, v in h.items():
                        category_key.append(k)
                category_key = list(set(category_key))
                # print(category_key)
                
        
                
                
                """
                bar plot data with schema string:integer
                """
                string_integer_data = []
                for e in category_key:
                    f = []
                    for j in string_integer:
                        for k, v in j.items():
                            if e == k:
                                f.append(v)
                    string_integer_data.append({e: f})
                # print(string_integer_data)
        
                
                """
                extract string float map
                """
                string_float = []
                for i in result:
                    for j in i['result']:
                        if "type" in j["endnode"]:
                            if j['startnode']['type'] == "STRING" and j['endnode']['type'] == "FLOAT":
                                string_float.append({j["endnode"]['category'] : {"key" : j['startnode']['text'], "value":j["endnode"]['text']}})
                                # print({j["endnode"]['category'] : {j['startnode']['text']:j["endnode"]['text']}})
                      
                """
                Category key:pair for string_float
                """
                category_key_sf = []
                for h in string_float:
                    for k, v in h.items():
                        category_key_sf.append(k)
                category_key_sf = list(set(category_key_sf))
                # print(category_key)
                
        
                
                
                """
                bar plot data with schema string:float
                """
                string_float_data = []
                for e in category_key_sf:
                    f = []
                    for j in string_float:
                        for k, v in j.items():
                            if e == k:
                                f.append(v)
                    string_float_data.append({e: f})
                # print(string_float_data)
                
                
                """
                extract datetime integer map
                """
                datetime_integer = []
                for i in result:
                    for j in i['result']:
                        if "type" in j["endnode"]:
                            if (j['startnode']['type'] == 'LocalDate' and j['endnode']['type'] == "INTEGER") or (j['startnode']['type'] == "INTEGER"  and j['endnode']['type'] == 'LocalDate'):
                                datetime_integer.append({j["endnode"]['category'] : {"key" : str(j['startnode']['text']), "value":str(j["endnode"]['text'])}})
                                # print({j["startnode"]['category'] : {j['startnode']['text']:j["endnode"]['text']}})
                      
                """
                Category key:pair for datetime integer
                """
                category_key_di = []
                for h in datetime_integer:
                    for k, v in h.items():
                        category_key_di.append(k)
                category_key_di = list(set(category_key_di))
                # print(category_key)
                
        
                
                
                """
                bar plot data with schema datetime:integer
                """
                datetime_integer_data = []
                for e in category_key_di:
                    f = []
                    for j in datetime_integer:
                        for k, v in j.items():
                            if e == k:
                                f.append(v)
                    datetime_integer_data.append({e: f})
                # print(datetime_integer_data)
        
                
                """
                extract string:string map
                """
                string_string = []
                for i in result:
                    for j in i['result']:
                        if "type" in j["endnode"]:
                            if j['startnode']['type'] == 'STRING' and j['endnode']['type'] == "STRING":
                                # print([j["startnode"]["link"], j["startnode"]["source"]])
                                if (j["startnode"]['category'] != "Country") and (j["startnode"]['category'] != "STATE_OR_PROVINCE"):
                                    if "links" in j["startnode"] or "source" in j["startnode"]:
                                        string_string.append({j["startnode"]['category'] : {"key" : j['startnode']['text'], "value":j["endnode"]['text'], "source":  j["startnode"]['source'], "links" : j["startnode"]["links"]}})
                                    
                                        # print({j["startnode"]["links"]: j["startnode"]['source']})
                                # print({j["startnode"]['category'] : {j['startnode']['text']:j["endnode"]['text']}})
                      
                """
                Category key:pair for string:string
                """
                category_key_string = []
                for h in string_string:
                    for k, v in h.items():
                        category_key_string.append(k)
                category_key_string = list(set(category_key_string))
                # print(category_key)
                
        
                
                
                """
                bar plot data with schema string:string
                """
                string_string_data = []
                for e in category_key_string:
                    f = []
                    for j in string_string:
                        for k, v in j.items():
                            if e == k:
                                f.append(v)
                    string_string_data.append({e: f})
        
        
                
                
                
                
                sorted_category = []
                for j in take_category:
                    d = []
                    for i in create_object:  
                        for k, v in i.items():
                            if j == k:
                                d.append(v)
                    sorted_category.append({j: d})
        
                query = """
                CALL db.index.fulltext.queryRelationships("tags", $search_input) YIELD relationship, score
                where score > 3
                match (node)-[relationship]-(b)
                //UNWIND keys(node) as key unwind keys(b) as f
                with labels(node) as v, node, b
                with collect(distinct v[0]) as category, node.text as tx, b.text as bt
                RETURN category, tx
                """
                
                 
                q = """
                CALL db.index.fulltext.queryRelationships("tags", $search_input) YIELD relationship, score
                where score > 3
                match path =  (node)-[relationship]-(b)
                unwind nodes(path) as p unwind relationships(path) as r
                // RETURN {nodes: collect(distinct p), links: collect(DISTINCT {source: id(startNode(r)), target: id(endNode(r))})}
                UNWIND keys(p) as key
                //RETURN collect(distinct {name:p[key]}) as nodes, collect(DISTINCT {source: id(startNode(r)), target: id(endNode(r))}) as links
                return collect(distinct properties(p)) as nodes, collect(DISTINCT {source: id(startNode(r)), target: id(endNode(r))}) as links
                """
                t = sendToNeo4j(q, search_input=text)
        
                output = sendToNeo4j(query, search_input=text)
                # print(output)
                out_category = [i['category'][0] for i in output if i['category'][0] != "ABSTRACT" if i['category'][0] != "COVID" if i['category'][0] != "Incidence_Rate" if i['category'][0] != "CONFIRMED" if i['category'][0] != 'FATALITY_RATE' if i['category'][0] != 'Confirmed' if i['category'][0] != 'Death' ]
                out_category_list = list(set(out_category))
                # print(out_category_list)
                category = [{cat['category'][0]:cat['tx']} for cat in output if  cat['category'][0]]
                return render_template('search-result.html', output=out_category_list, result=result, take_category=sorted_category, create_object=create_object, string_integer_data=string_integer_data, datetime_integer_data=datetime_integer_data, string_float_data=string_float_data, string_string_data=string_string_data, text=text)
        

        """
        get start node an endnote then extract category(unique) if len(str(j['startnode']['text'])) < 15
        """
        category_table = [j['startnode']['category'] + ":" + j["endnode"]['category'] for i in result for j in i['result'] if type(j['startnode']['text']) != list   if j['startnode']['text'] != "Unknown" if j['endnode']['text'] != "Unknown"]
        take_category = list(set(category_table))

        """
        object with category:text map
        """
        create_object = [{j['startnode']['category'] + ":" + j["endnode"]['category'] : str(j['startnode']['text']) + ":" + str(j["endnode"]['text'])} for i in result for j in i['result'] if "text" in j["endnode"] if "type" in j["endnode"] if type(j['startnode']['text']) != list ]
        
        """
        extract string integer map
        """
        string_integer = []
        for i in result:
            for j in i['result']:
                if "type" in j["endnode"]:
                    if j['startnode']['type'] == "STRING" and j['endnode']['type'] == "INTEGER":
                        string_integer.append({j["endnode"]['category'] : {"key" : j['startnode']['text'], "value":j["endnode"]['text']}})
                    # print({j["endnode"]['category'] : {j['startnode']['text']:j["endnode"]['text']}})
              
              
        """
        Category key:pair
        """
        category_key = []
        for h in string_integer:
            for k, v in h.items():
                category_key.append(k)
        category_key = list(set(category_key))
        # print(category_key)
        

        
        
        """
        bar plot data with schema string:integer
        """
        string_integer_data = []
        for e in category_key:
            f = []
            for j in string_integer:
                for k, v in j.items():
                    if e == k:
                        f.append(v)
            string_integer_data.append({e: f})
        # print(string_integer_data)

        
        """
        extract string float map
        """
        string_float = []
        for i in result:
            for j in i['result']:
                if "type" in j["endnode"]:
                    if j['startnode']['type'] == "STRING" and j['endnode']['type'] == "FLOAT":
                        string_float.append({j["endnode"]['category'] : {"key" : j['startnode']['text'], "value":j["endnode"]['text']}})
                        # print({j["endnode"]['category'] : {j['startnode']['text']:j["endnode"]['text']}})
              
        """
        Category key:pair for string_float
        """
        category_key_sf = []
        for h in string_float:
            for k, v in h.items():
                category_key_sf.append(k)
        category_key_sf = list(set(category_key_sf))
        # print(category_key)
        

        
        
        """
        bar plot data with schema string:float
        """
        string_float_data = []
        for e in category_key_sf:
            f = []
            for j in string_float:
                for k, v in j.items():
                    if e == k:
                        f.append(v)
            string_float_data.append({e: f})
        # print(string_float_data)
        
        
        """
        extract datetime integer map
        """
        datetime_integer = []
        for i in result:
            for j in i['result']:
                if "type" in j["endnode"]:
                    if (j['startnode']['type'] == 'LocalDate' and j['endnode']['type'] == "INTEGER") or (j['startnode']['type'] == "INTEGER"  and j['endnode']['type'] == 'LocalDate'):
                        datetime_integer.append({j["endnode"]['category'] : {"key" : str(j['startnode']['text']), "value":str(j["endnode"]['text'])}})
                        # print({j["startnode"]['category'] : {j['startnode']['text']:j["endnode"]['text']}})
              
        """
        Category key:pair for datetime integer
        """
        category_key_di = []
        for h in datetime_integer:
            for k, v in h.items():
                category_key_di.append(k)
        category_key_di = list(set(category_key_di))
        # print(category_key)
        

        
        
        """
        bar plot data with schema datetime:integer
        """
        datetime_integer_data = []
        for e in category_key_di:
            f = []
            for j in datetime_integer:
                for k, v in j.items():
                    if e == k:
                        f.append(v)
            datetime_integer_data.append({e: f})
        # print(datetime_integer_data)

        
        """
        extract string:string map
        """
        string_string = []
        for i in result:
            for j in i['result']:
                if "type" in j["endnode"]:
                    if j['startnode']['type'] == 'STRING' and j['endnode']['type'] == "STRING":
                        # print([j["startnode"]["link"], j["startnode"]["source"]])
                        if (j["startnode"]['category'] != "Country") and (j["startnode"]['category'] != "STATE_OR_PROVINCE"):
                            if "links" in j["startnode"] or "source" in j["startnode"]:
                                string_string.append({j["startnode"]['category'] : {"key" : j['startnode']['text'], "value":j["endnode"]['text'], "source":  j["startnode"]['source'], "links" : j["startnode"]["links"]}})
                            
                                # print({j["startnode"]["links"]: j["startnode"]['source']})
                        # print({j["startnode"]['category'] : {j['startnode']['text']:j["endnode"]['text']}})
              
        """
        Category key:pair for string:string
        """
        category_key_string = []
        for h in string_string:
            for k, v in h.items():
                category_key_string.append(k)
        category_key_string = list(set(category_key_string))
        # print(category_key)
        

        
        
        """
        bar plot data with schema string:string
        """
        string_string_data = []
        for e in category_key_string:
            f = []
            for j in string_string:
                for k, v in j.items():
                    if e == k:
                        f.append(v)
            string_string_data.append({e: f})


        
        
        
        
        sorted_category = []
        for j in take_category:
            d = []
            for i in create_object:  
                for k, v in i.items():
                    if j == k:
                        d.append(v)
            sorted_category.append({j: d})

        query = """
        CALL db.index.fulltext.queryRelationships("tags", $search_input) YIELD relationship, score
        where score > 3
        match (node)-[relationship]-(b)
        //UNWIND keys(node) as key unwind keys(b) as f
        with labels(node) as v, node, b
        with collect(distinct v[0]) as category, node.text as tx, b.text as bt
        RETURN category, tx
        """
        
         
        q = """
        CALL db.index.fulltext.queryRelationships("tags", $search_input) YIELD relationship, score
        where score > 3
        match path =  (node)-[relationship]-(b)
        unwind nodes(path) as p unwind relationships(path) as r
        // RETURN {nodes: collect(distinct p), links: collect(DISTINCT {source: id(startNode(r)), target: id(endNode(r))})}
        UNWIND keys(p) as key
        //RETURN collect(distinct {name:p[key]}) as nodes, collect(DISTINCT {source: id(startNode(r)), target: id(endNode(r))}) as links
        return collect(distinct properties(p)) as nodes, collect(DISTINCT {source: id(startNode(r)), target: id(endNode(r))}) as links
        """
        t = sendToNeo4j(q, search_input=text)

        output = sendToNeo4j(query, search_input=text)
        # print(output)
        out_category = [i['category'][0] for i in output if i['category'][0] != "ABSTRACT" if i['category'][0] != "COVID" if i['category'][0] != "Incidence_Rate" if i['category'][0] != "CONFIRMED" if i['category'][0] != 'FATALITY_RATE' if i['category'][0] != 'Confirmed' if i['category'][0] != 'Death' ]
        out_category_list = list(set(out_category))
        # print(out_category_list)
        category = [{cat['category'][0]:cat['tx']} for cat in output if  cat['category'][0]]
        return render_template('search-result.html', output=out_category_list, result=result, take_category=sorted_category, create_object=create_object, string_integer_data=string_integer_data, datetime_integer_data=datetime_integer_data, string_float_data=string_float_data, string_string_data=string_string_data, text=text)
        
            

"""display graph"""
@app.route("/graph/<string:text>/", methods=["POST", "GET"])
def subgraph(text):
    # print(text)
    filter_query = """
    MATCH (a {text:$text})-[r]-(b)
    CALL apoc.path.subgraphAll(a, {maxLevel:4}) YIELD nodes, relationships
    unwind relationships as rel
    unwind nodes as node
    return collect(distinct properties(node)) as nodes, collect(Distinct {source:id(startNode(rel)), target:id(endNode(rel))}) as links
    """
    filtered_result = sendToNeo4j(filter_query, text=text)
    # print(filtered_result)
#    return jsonify(filtered_result)
    return render_template('graph.html', filtered_result=filtered_result)
    
@app.route('/file', methods=['POST'])
def save_img():
    if request.method == "POST":
        
        file_uploaded = request.files['file']
        filename = secure_filename(file_uploaded.filename)
        file_uploaded.save('upload/' + filename)
        run_spark_pipeline(os.path.join("upload/", filename))
        return redirect(url_for('index'))
#         result.wait()  # 65



if __name__ == "__main__":
    app.jinja_env.filters['split_space'] = split_space
    app.run(host="0.0.0.0", port=8181)
    
#text = request.form['text']
