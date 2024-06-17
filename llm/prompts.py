CYPHER_GENERATION_TEMPLATE = """Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.

DO NOT ALLOW DELETE, INSERT, UPDATE queries. In that case, say this is not allowed, contacting system administrator.

Do not use any other relationship types or properties that are not provided.
Schema:
{schema}
This is important. if it mentions ID, that means external_id field.

When returning the modelcard or model information, return the external_id instead of the name.

If a model needs to refer to accuracy, it  usually refers to the accuracy information in the AI_MODEL associated with the model card. You can use a query like this to get that information linking the model card with technical information.  For example, to get the highest accuracy models:
match(mc:ModelCard)-[]->(ai:AIModel)
with mc.external_id as mcid, ai.test_accuracy as test_accuracy
order by test_accuracy DESC
limit 1
Return mcid, test_accuracy

But if it's deployment related, use the mean_accuracy in the deployment nodes instead.

Bias or fairness information about a model card is contained in the BIAS_ANALYSIS associated with the model card.

Devices does not have a name field. d.name is equal to d.device_id. Use that instead.
When querying for device, use the name of the device in the device_id field.

when returning model cards or models, remove the v_embedding field. Do not include that in results.

For devices, use the given name in the external_id field.

To getting similar to or closest to models, you can compare the model cards embedding field using cosine similarity.
Here's an example query to run to get the similar or close models. I've added <> for variables you can change.
MATCH (mc:ModelCard external_id: <id>)
                WITH mc.embedding AS given_embedding
                CALL db.index.vector.queryNodes('embedding', <num of results>, given_embedding) yield node, score
                RETURN score, node.external_id AS id

To get the model with the best fairness you can use the following query.

match(n:ModelCard)-[]->(f:BiasAnalysis)
with n, ABS(f.demographic_parity_diff) as dem, ABS(f.equal_odds_difference) as eq
ORDER BY dem + eq ASC
Limit 1
Return n.external_id, dem, eq

When calculating lowest values for demographic_parity_difference or equal_odds_difference, refer to the absolute value.

If prompted about framework or license, refer to the corresponding AI_MODEL to get the information.

if you can't find the answer or do not know the answer return "it's not available in the database.
ONLY RETURN THE CYPHER QUERY!

The question is:
{question}"""


QA_TEMPLATE = """Task:Generate a response to the question only using the provided context.

The context contains information retrieved from running a query corresponding to the question.
Generate a text based answer to the question imitating a human answering. Limit the response to one sentence.

The context is:
{context}

The question is:
{question}"""

LLM_template = """Your job is to answer the question below.
{question}
"""