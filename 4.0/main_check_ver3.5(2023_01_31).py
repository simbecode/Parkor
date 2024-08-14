#2022년 5월 14일 미세먼지데이터갯수 문제있는것만 출력하도로고 변경
#2022년 6월 1일  휘발성유기화합물 값이 더 높게 나오는 지점 검출, 0값 나오는 지점 검출 추가
#2022년 6월 21일 휘발성유기화합물 값이 더클경우 최근 10개데이터만 출력, 데이터값이 부족할 경우 에러 예외처리함 
#2022년 6월 27일 referenced before assignment 변수에러 발생해서 글로벌변수 추가, 데이터검출 발생알람 변경, 프로그램실행문구 추가
#2022년 6월 30일 svc값이 높을대 나오는 값 10에서 20개로 변경, pm값에 관측시간 추가
#2022년 8월 24일 제로값나오는 문구 수정 후 재배포
#2022년 11월 12일 데이터값 전체적으로 검토후 한번에 표출하도록 수정완료  
#2022년 12월 19일 춘천지점, 충주지점 추가, 대구_주거, 대구_산단 지점번호 홈페이지기준으로 수정 
#2023년 1월 2일 svc값이 dry값보다 클경우 생기는 값이 한시간동안 지속적일경우에만 표출하도록 변경
#2023년 1월 5일 드라이어값보다 svc값이 높으거 체크를 못해서 그 부분 수정 
#2023년 1월 11일 종로지점 추가 , 1월 19일 구미지점 추가
#2023년 1월 31일 23년도 추가설치지점 모두 추가 
from itertools import count
from time import sleep
from numpy import append
from tqdm import tqdm
import requests
import pandas as pd
import datetime as dt
import time
import math
from itertools import zip_longest

print("프로그램이 실행되었습니다. ")

# 데이터 갯수 출력
final_count_data_name = []
final_count_data = []

# 통합센서 문제 출력
final_weather_state = []

# 제로데이터 
final_zero_state = []

# 드라이어 > svc 값
final_under_date = []
final_under_date_value = []

def get_data(area, page, start, end):
    url = "http://aican.nifos.go.kr/data/pastInfoVw.do"
    params =    {
    "obsrrTpCd": area,
    "pageIndex": page,
    "fromDate": start,
    "toDate": end
    }
    resp = requests.post(url=url, data=params)
    tables = pd.read_html(resp.text)
    return tables[0]

def get_judge_data(data_concat,bad_area):
    
    global result_data
    time_data = data_concat[['관측시간']]
    minus_time_data = time_data[:-2]                                                                           # 데이터타임 -2
    result_nancheck = data_concat[['온도(℃)','습도(%)','풍속(㎧)','풍향(degree)']]                            #데이터값 분류
    normal_data = data_concat[['산림 미세먼지 농도','산업유래 휘발성유기화합물 미세먼지 농도']]                 #데이터값 분류
    normal_data = normal_data[:-2]                                                                             #조회이력이없습니다. 제거
    normal_data.columns = ['col1','col2','col3','col4','col5','col6']                                          #열이름 재설정
    sub1_data = normal_data[['col1','col2','col3']]                                                            #산림미세먼지 값재설정
    sub2_data = normal_data[['col4','col5','col6']]                                                            #휘발성유기화합물 미세먼지농도
    sub2_data.columns =  ['col1','col2','col3']                                                                #차를 구하기위해서 컬럼명통일
    try:
        result_data = sub1_data.sub(sub2_data)                                                                     #산림미세먼지와 휘발성유기화합물 차구하기
    except:
        pass
    
    result_data.columns = ['pm10','pm2.5','pm1.0']                                                             #컬럼명 정의
    time_add_result_data = pd.concat([minus_time_data,result_data],axis=1)                                     #시간추가한 마이너스를 구한 값
    condition_under = (result_data < 0).any()                                                                        #차를 구한 결과값에서 -값확인 
    condition_zero = (normal_data == 0).any()                                                                        #데이터값에 제로값이있는지 확인 
    check_for_nan = result_nancheck.isnull().values.any()                                                     # 데이터값에 nan값이 있으면 true로 변경
    data_index_cnt = (len(data_concat.index))
    
    result_data_tail_6 = result_data.tail(6)    
    final_result_data_tail_6 = (result_data_tail_6 < 0).any() 
    final_plus_result_data_tail_6 = (result_data_tail_6 > 0).any() 

    

    
    if data_index_cnt < values_cnt-5: # -1 홈페이지에서 10분 늦게올라와서 -1을 해야 정상값
        # print(bad_area)
        # dust_state = "미세먼지데이터를 확인해주세요"
        # print(dust_state)
        # print("--------------today_data_cnt :", data_index_cnt,"--------------now_data_cnt", values_cnt-2)
        final_count_data_name.append(bad_area)
        final_count_data_name.append(data_index_cnt)
        
        # print("현재 데이터갯수 :",values_cnt-2)

    if condition_zero['col1'] |condition_zero['col2'] | condition_zero['col3']|condition_zero['col4'] |condition_zero['col5'] | condition_zero['col6']:                          #데이터값에 음수가있으면 출력한다.
        # print(bad_area)
        # print("00000000000000000000000000제로값을 확인해하세요000000000000000000000000000000")
        final_zero_state.append(bad_area)    

    if condition_under['pm10'] |condition_under['pm2.5'] | condition_under['pm1.0']:                          #데이터값에 음수가있으면 출력한다.
        if final_result_data_tail_6['pm10'] | final_result_data_tail_6['pm2.5'] | final_result_data_tail_6['pm1.0']:
            if final_plus_result_data_tail_6['pm10'] | final_plus_result_data_tail_6['pm2.5'] | final_plus_result_data_tail_6['pm1.0']:

                pass
            
            else:
                final_under_date.append(bad_area)
                final_under_date.append(time_add_result_data.tail(6))
            
        # print(bad_area)
        # print("휘발성유기화합물 값이 더 큽니다. ")
        # print(time_add_result_data.tail(20))


    
    if check_for_nan == True:
        # print(bad_area)
        # weather_state = "***********************통합센서데이터를 확인해주세요"
        # print(weather_state)
        
        final_weather_state.append(bad_area)

    # print(bad_area)
    # print(dust_state)
    # print(weather_state)
    time.sleep(0.1)
    


total_area = [ 
            "0011","0012","0013",   #홍릉_도심,     홍릉_숲내부_5m,     홍릉_숲내부20m
            "0021","0022","0023",   #고매_도로,     고매_50m,           고매_150m
            "0031","0032","0033",   #시화_산단,     시화_차단숲,        시화_주거
            "0041","0042","0043",   #양재_도로,     양재_200m,          양재_300m
            "0051","0052","0053",   #관악_도심,     관악_캠퍼스,         관악_숲
            "0061","0062","0063",   #제주_5m,       제주_10m,           제주_20m
            "0071","0072","0073",   #고양_산단,      고양_주거,          고양_숲
            "0081","0082","0083",   #기장_산단,      기상_숲,            기장_주거
            "0091","0092","0093",   #평창_5m,        평창_20m,           평창_30m
            "0101","0102","0103",   #횡성_5m,        횡성_20m,           횡성_30m
            "0111","0112","0113",   #남산_5m,        남산_13.5m,          남산_25.5m
            "0121","0122","0123",   #남산_숲,        남산_고개,           남산_자락
            "0131","0132","0133",   #전주_산단,      전주_주거1,          전주_주거2
            "0141","0142","0143",   #인천_해안,       인천_주거1,         인천_주거2
            "0151","0152","0153",   #인천_산단,       인천_완충,          인천_주거
            "0161","0162","0163",   #울산_산단,       울산_숲,            울산_주거
            "0171","0172","0173",   #태안_산단,       태안_숲,            태안_주거
            "0181","0182","0183",   #광주_산단,       광주_숲,            광주_주거
            "0191","0192","0193",   #대구_산단,       대구_주거,          대구_강가
            "0201","0202","0203",   #대전_산단,       대전_주거1,         대전_주거2          
            "0211","0212","0213",   #나주_오염,       나주_주거,          나주_산림
            "0221","0222","0223",   #세종_도시,       세종_주거,          세종_숲
            "0231","0232","0233",   #강릉_산림,       강릉_주거,          강릉_해안
            "0241","0242","0243",   #양구_국외(산림)  양구_주거,           양구_산림
            "0251","0252","0253",   #연천_국외(산림), 연천_주거,           연천_파주(산림)
            "0261","0262","0263",   #순천_여수(공단), 순천_차단숲,         순천_주거
            "0271","0272","0273",   #칠곡_도심(산단), 칠곡_주거,           칠곡_산림
            "0281","0282","0283",   #예산_산단,       예산_주거,           예산_산림
            "0291","0292","0293",   #완도_지상,      완도_15M,            완도_30
            "0301","0302","0303",   #충주_산단,       충주_주거,           충주_산림
            "0311","0312","0313",   #춘천 주거1,      춘천_주거2,          춘천_산림      
            "0321","0322","0323",   #종로_도심,      종로_주거,            종로_숲      
            "0331","0332","0333",   #구미_산단,      구미_주거2,            구미_산림
            "0341","0342","0343",   #삼척_동해_주거1,삼척_동해_주거2,       삼척_동해_산림
            "0351","0352","0353",   #양간지대_주거1  양간지대_주거2,         양간지대_숲
            "0361","0362","0363",   #청주_산단,      청주_주거2,            청주_숲
            
            ]


     
time_value_H = int(dt.datetime.now().strftime('%H'))
time_value_M = int(dt.datetime.now().strftime('%M'))
values_cnt = math.floor(time_value_H*6 + time_value_M*0.1) # 현재시 + 분 , 한개빠지는 지역 30개, 세개빠지는 지역 2개 2022-05-01기준
page = math.ceil(time_value_H * 0.6) # 한페이지당 10개 

start = dt.datetime.now().strftime('%Y-%m-%d')
end = dt.datetime.now().strftime('%Y-%m-%d')

for i in tqdm(total_area):   
    
    if i =="0011":
        
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end))    
        data_concat = pd.concat(df_list,ignore_index=True)
        
        bad_area = "홍릉_도심"
        get_judge_data(data_concat, bad_area)
        
        

    elif i == "0012":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)           

        bad_area = "홍릉_숲내부5m"
        get_judge_data(data_concat, bad_area)
   
             

    elif i == "0013":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)           

        bad_area = "홍릉_숲내부20m"
        get_judge_data(data_concat, bad_area)
            
            
            
    elif i =="0021":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)           

        bad_area = "고매_도로"
        get_judge_data(data_concat, bad_area)
           
    
    elif i == "0022":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)           

        bad_area = "고매_50m"
        get_judge_data(data_concat, bad_area)    

    elif i == "0023":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "고매_150m"
        get_judge_data(data_concat, bad_area)    
            
    elif i =="0031":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "시화_산단"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0032":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "시화_차단숲"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0033":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "시화_주거"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0041":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "양재_도로"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0042":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "양재_200m"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0043":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "양재_300m"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0051":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "관악_도심"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0052":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "관악_캠퍼스"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0053":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "관악_숲"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0061":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "제주_5m"
        get_judge_data(data_concat, bad_area)    
        
    elif i == "0062":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "제주_10m"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0063":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "제주_20m"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0071":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "고양_산단"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0072":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "고양_주거"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0073":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "고양_숲"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0081":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "기장_산단"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0082":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "기장_숲"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0083":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "기장_주거"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0091":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "평창_5m"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0092":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "평창_20m"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0093":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "평창_30m"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0101":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "횡성_5m"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0102":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "횡성_20m"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0103":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "횡성_30m"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0111":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "남산_5m"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0112":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "남산_13.5m"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0113":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "남산_25.5m"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0121":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "서울_숲"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0122":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "서울_고개"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0123":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "서울_자락"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0131":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "전주_산단"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0132":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "전주_주거1"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0133":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "전주_주거2"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0141":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "송도_해안"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0142":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "송도_주거1"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0143":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "송도_주거2"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0151":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "석남_산단"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0152":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "석남_완충"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0153":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "석남_주거"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0161":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "울산_산단"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0162":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "울산_숲"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0163":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "울산_주거"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0171":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "태안_산단"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0172":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "태안_숲"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0173":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "태안_주거"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0181":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "광주_산단"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0182":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "광주_숲"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0183":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "광주_주거"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0191":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "대구_주거"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0192":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "대구_산단"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0193":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "대구_강가"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0201":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "대전_산단"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0202":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "대전_주거1"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0203":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "대전_주거2"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0211":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "나주_오염"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0212":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "나주_주거"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0213":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "나주_산림"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0221":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "세종_도시"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0222":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "세종_주거"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0223":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "세종_숲"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0231":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "강릉_산림"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0232":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "강릉_주거"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0233":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "강릉_해안"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0241":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "양구_국외(산림)"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0242":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "양구_주거"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0243":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "양구_산림"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0251":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "연천_국외(산림)"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0252":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "연천_주거"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0253":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "연천_파주(산림)"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0261":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "순천_여수(공단)"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0262":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "순천_차단숲"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0263":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "순천_주거"
        get_judge_data(data_concat, bad_area)    
                
    elif i =="0271":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "칠곡_도심(산단)"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0272":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "칠곡_주거"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0273":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "칠곡_산림"
        get_judge_data(data_concat, bad_area)    
        
    elif i =="0281":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "예산_산단"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0282":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "예산_주거"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0283":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "예산_산림"
        get_judge_data(data_concat, bad_area)    

    elif i =="0291":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "완도_지상"
        get_judge_data(data_concat, bad_area)    
    
    elif i == "0292":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "완도_15m"
        get_judge_data(data_concat, bad_area)    
            

    elif i == "0293":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "완도_30m"
        get_judge_data(data_concat, bad_area)    

    elif i == "0301":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "충주_산단"
        get_judge_data(data_concat, bad_area)    

    elif i == "0302":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "충주_주거"
        get_judge_data(data_concat, bad_area)    

    elif i == "0303":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "충주_산림"
        get_judge_data(data_concat, bad_area)    
                
    elif i == "0311":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "춘천_주거1"
        get_judge_data(data_concat, bad_area)    

    elif i == "0312":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "춘천_주거2"
        get_judge_data(data_concat, bad_area)    

    elif i == "0313":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "춘천_산림"
        get_judge_data(data_concat, bad_area)    
                
    elif i == "0321":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "종로_도심"
        get_judge_data(data_concat, bad_area)    

    elif i == "0322":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "종로_주거"
        get_judge_data(data_concat, bad_area)    

    elif i == "0323":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "종로_숲"
        get_judge_data(data_concat, bad_area)
        
    elif i == "0331":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "구미_산단"
        get_judge_data(data_concat, bad_area)    

    elif i == "0332":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "구미_주거"
        get_judge_data(data_concat, bad_area)    

    elif i == "0333":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "구미_산림"
        get_judge_data(data_concat, bad_area)    
        
    elif i == "0341":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "삼척_동해_주거1"
        get_judge_data(data_concat, bad_area)    

    elif i == "0342":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "삼척_동해_주거2"
        get_judge_data(data_concat, bad_area)    

    elif i == "0343":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "삼척_동해_산림"
        get_judge_data(data_concat, bad_area)    

    elif i == "0351":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "양간지대_주거1"
        get_judge_data(data_concat, bad_area)    

    elif i == "0352":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "양간지대_주거2"
        get_judge_data(data_concat, bad_area)    

    elif i == "0353":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "양간지대_숲"
        get_judge_data(data_concat, bad_area)    
        
        
    elif i == "0361":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "청주_산단"
        get_judge_data(data_concat, bad_area)    

    elif i == "0362":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "청주_주거"
        get_judge_data(data_concat, bad_area)    

    elif i == "0363":
        df_list=[]
        for j in range(page):      
            df_list.append(get_data(i,  j+1, start, end)) 
        data_concat = pd.concat(df_list,ignore_index=True)        
        
        bad_area = "청주_숲"
        get_judge_data(data_concat, bad_area)    
       
        
        
print("--완료--")
print("현재시간 데이터수 : ", values_cnt)
print(final_count_data_name, final_count_data)
print("제로값을 확인하세요 : ", final_zero_state)
print("통합센서에 문제 : ", final_weather_state)
print("휘발성유기화합물 값이 더 큽니다. ")
print(final_under_date)

print("엔터를 누르면 종료됩니다.")
x = input()

# time.sleep(6000) 

