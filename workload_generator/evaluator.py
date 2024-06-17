from parser.json_mc_parser import parse_json_mc
from ingester.neo4j_ingester import MCIngester
import copy
import uuid
import random
import json
import time
from datetime import datetime, timedelta

def main():
    uri = "bolt://localhost:7689"
    user = "neo4j"
    password = "rootroot"
    # password = "q?fRLl%L^y7M"

    mc_ingester = MCIngester(uri, user, password)

    model_card = parse_json_mc("../examples/model_cards/uci_cnn_mc.json")
    model_card['external_id'] = "8094377c-33a7-4fbd-a4ea-01e21a763dc9"

    num_runs = 1
    indexed_time = 0
    non_indexed_time = 0
    for i in range(num_runs):
        random_embedding = [random.uniform(-0.05, 0.05) for _ in range(300)]
        # random_embedding = [0.020796116453607877,0.034645143421768804,-0.004321020307692859,0.013646549870170638,0.03423100784911415,-0.03949833287553624,-0.0136174633906187,-0.04201828964044534,0.04266372036717185,-0.030819608868891346,0.0018857033208382196,-0.04701900306779221,-0.012067597072948633,-0.03834049882836511,0.0008705389632840399,-0.031690435507703764,-0.03303871160752503,0.01309064375804353,-0.031019476691944603,-0.010782482815781515,0.021288417553986458,-0.03245084458192922,-0.023736325747951727,-0.022747557161849397,0.04592951546759626,0.00926301114311747,0.0429589112809356,0.015399225989682283,-0.032372350154486196,0.04427690895710765,0.002778977025384523,-0.04529867681601155,-0.032793997435624056,0.016141946889549258,-0.021156765268429814,-0.01077597867253964,0.03285120427442377,0.003009401696922376,0.010770705684512515,0.029092724190259517,-0.03181130722130249,0.04980472450427194,0.008859185876180675,0.017572568559924492,0.004675417537189433,-0.005865284790329828,-0.02825086271661216,-0.043789935134785074,0.04883865388396458,-0.027652652631783195,0.016978618885384184,0.022330891766300404,0.024159409605065324,-0.03461643357450605,-0.03641086396449748,0.028002340200517117,-0.029683966569078027,-0.04409485033829992,0.04028971963296839,0.04208162969199404,0.009251778303054493,0.02203597923189092,0.04874328770833947,0.021893512460164077,-0.03910115434757405,0.04180379862903952,-0.03919134107808232,-0.045038629681503996,-0.013689155745128148,-0.02788391781374472,-0.023675739021830258,0.01383491248923488,-0.021812312718054918,-0.007783013716951691,-0.0034077737081431997,0.04667573564052287,0.04975768919022569,0.008426275228531142,-0.04995289144772191,0.04874427271261737,0.02567235814985734,-0.0360859928277546,0.020588339944919515,-0.01653039669519514,0.03088767791103403,0.007620173509989524,-0.04464638308347288,-0.0492730092135325,-0.019864628461838764,0.02308169504260836,-0.04360178578264291,0.0021115141483203925,0.029042665175395527,-0.015353685115163489,0.034892459050080024,0.0010506264177066113,0.024375161604533443,-0.00745045603395561,0.04425885660688614,-0.02443541760336533,-0.02783465676614616,0.020306962164163417,0.01096060801340247,0.04062219627252116,-0.005921423946510837,-0.012121352389778031,0.0045547292421253965,-0.004045265102352605,-0.007190661106066844,-0.006581750942742257,0.04723126636293716,-0.003792678015782036,-0.02837292416670846,-0.003930192035413685,0.005376461035068579,-0.0023944015020148993,-0.047100635784461886,0.019287108391752433,0.031528670007862344,0.032925173377527664,-0.023012225704720557,-0.04855676240568371,0.004179310705533144,0.02935862944106246,0.0364350386056464,-0.032533037353582775,0.032168899364937165,0.04460195017450368,0.024902401735723237,0.00062248940014209,-0.010831422831863224,-0.04348653478961865,0.04796852603422666,0.027913234004472,0.022331342280630495,0.008676213061419871,0.02149501730502261,0.007774849489721493,0.02899696959762081,-0.009988207830194565,0.03144556680264049,0.007738970237535225,-0.03851443644208983,-0.01804288344963989,-0.00397730200498729,-0.004864695474838435,0.024098481757679563,-0.013969274527019813,-0.010645666958378298,0.036927715306669884,-0.011003411103038485,-0.02061835685407234,0.00019230379573365042,-0.027267205969436572,0.028084786029554762,0.0011612703671395191,0.007366892362481101,0.03683953339304959,0.0029104821455810392,-0.04335751823961338,-0.01707366992750866,-0.02985672899245785,0.01500841965786287,-0.043411809498737845,-0.026284679612019704,-0.019172467884450674,0.02625714650178708,0.01558032972332185,-0.007052368822239016,0.028233629702180227,-0.04678566879939386,-0.009001049101029446,0.011236782571551807,-0.03385952218227293,-0.024800031624052223,-0.0017468921217542177,-0.0005774030613093437,-0.020792308035805864,-0.03336926572040362,-0.0063603800889473275,0.004126752154787652,0.0499905850987674,-0.015145910601410253,0.018588375735850718,-0.04227753458469315,-0.016772700330528113,-0.025131677197742532,-0.04103883702332189,0.013744500615371524,-0.010585758294853628,-0.023431826753440035,0.01850986543342306,-0.034440770291079094,-0.04182078475559005,-0.04109729354970501,-0.033345948153437145,-0.04240120382445744,0.04134767539684013,-0.043949646615941175,-0.023454840783829214,-0.04975181198946892,-0.0067552364033016885,0.02604797733652607,-0.041765798602934646,0.006977268442640974,-0.018315262299540204,-0.0021673874208547814,0.022548322217273584,0.03122300496611055,0.046266067572460545,-0.01450466988037609,-0.027209262222802635,0.024765365834188258,0.016699352111098936,-0.0057751361750942865,-0.02468844637850286,0.017311541612898967,-0.005134518501689923,0.016845858265611774,0.03187750522987584,-0.03462458052329057,0.0465794327372273,-0.011620331014008375,-0.030876260009348636,0.015787532143943406,0.04285632093237696,-0.03537665516377351,-0.04864207208002844,-0.020933590899795088,0.02493926051522788,0.01084492404900611,0.0043233251303388745,0.020744280519167935,0.04418556537028935,0.02989164902725104,-0.032633693662126415,-0.036874463862194486,0.04758856451607721,-0.02428419188306077,-0.02228991556623157,0.04717498507830374,0.015049232013831834,0.025786203525325013,0.008048286123490248,-0.029063025731395423,-0.0449762856735231,-0.021385333680239416,0.01800448228296453,-0.009680993610685806,-0.005130116930202454,0.0032049627719545754,-0.03594318814743486,0.024385176337392428,0.02809205320492196,-0.027612938413210733,0.03450730788493761,-0.006004062195807423,0.03363515808784921,0.010069083266084522,-0.04064581196281472,-0.045940821144688906,-0.045072856850574564,-0.008566248350727015,-0.006010928345663948,0.0495040078320239,0.004528544729164384,-0.005700281257302674,0.005484387130877788,0.0432644818867247,0.04226729154250018,-0.00547187101027332,-0.011194851456957623,0.00490470230312471,-0.04990502322932153,0.02218711191760933,0.02793502405929743,0.035548290146490705,0.0022546665594343623,-0.02888201880474094,-0.0033602871353604832,0.0015695974049544231,0.04771534497737338,-0.0049620124382915715,0.03310105123182648,-0.025844802928341584,-0.020530000270118465,0.02142823506405929,-0.020580770823686024,0.004606129134660561,0.014787603514272801,-0.045048108163073745,-0.00550788647107061,-0.011285825513978755,0.026087294935558766,-0.04692607704333795,-0.0451294682819009,-0.006916878610679744,0.008310062366159013,0.039840191453642274,-0.027277408719609333]
        model_card['embedding'] = random_embedding
        model_card['v_embedding'] = random_embedding

        index_total_time, normal_total_time = mc_ingester.version_perf_test(model_card)
        indexed_time += index_total_time
        non_indexed_time += normal_total_time

    avg_indexed_time = indexed_time/num_runs
    avg_non_indexed_time = non_indexed_time/num_runs
    print("Index total time: {}\n normal total time: {}".format(avg_indexed_time, avg_non_indexed_time))

if __name__ == "__main__":
    main()