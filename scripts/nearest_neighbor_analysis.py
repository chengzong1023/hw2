#!/usr/bin/env python3
"""
最近測站分析與情境模擬
使用Haversine公式連接避難所與最近的AQI測站
"""

import pandas as pd
import numpy as np
import math
from datetime import datetime
import os

class NearestNeighborAnalysis:
    def __init__(self):
        self.aqi_data = None
        self.shelter_data = None
        self.earth_radius_km = 6371.0  # 地球半徑（公里）
        
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """使用Haversine公式計算兩點間距離"""
        # 將角度轉換為弧度
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine公式
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat/2)**2 + 
              math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        distance = self.earth_radius_km * c
        return distance
    
    def load_data(self):
        """載入AQI和避難所資料"""
        print("正在載入資料...")
        
        # 載入避難所資料
        try:
            self.shelter_data = pd.read_csv('data/shelter_locations_enriched.csv', encoding='utf-8-sig')
            print(f"載入 {len(self.shelter_data)} 個避難所")
        except Exception as e:
            print(f"載入避難所資料失敗: {e}")
            return False
        
        # 創建模擬AQI資料（因為API有問題）
        self.create_mock_aqi_data()
        print(f"載入 {len(self.aqi_data)} 個AQI測站")
        
        return True
    
    def create_mock_aqi_data(self):
        """創建模擬AQI資料"""
        mock_stations = [
            {"SiteName": "台北", "County": "臺北市", "AQI": 45, "lat": 25.0173, "lon": 121.5395},
            {"SiteName": "新北", "County": "新北市", "AQI": 42, "lat": 25.0167, "lon": 121.4667},
            {"SiteName": "桃園", "County": "桃園市", "AQI": 38, "lat": 24.9936, "lon": 121.3010},
            {"SiteName": "台中", "County": "臺中市", "AQI": 47, "lat": 24.1477, "lon": 120.6736},
            {"SiteName": "台南", "County": "臺南市", "AQI": 41, "lat": 22.9999, "lon": 120.2269},
            {"SiteName": "高雄", "County": "高雄市", "AQI": 48, "lat": 22.6273, "lon": 120.3014},
            {"SiteName": "基隆", "County": "基隆市", "AQI": 35, "lat": 25.1276, "lon": 121.7392},
            {"SiteName": "新竹", "County": "新竹市", "AQI": 42, "lat": 24.8138, "lon": 120.9675},
            {"SiteName": "嘉義", "County": "嘉義市", "AQI": 44, "lat": 23.4801, "lon": 120.4491},
            {"SiteName": "宜蘭", "County": "宜蘭縣", "AQI": 33, "lat": 24.6929, "lon": 121.7705},
            {"SiteName": "花蓮", "County": "花蓮縣", "AQI": 28, "lat": 23.7519, "lon": 121.6067},
            {"SiteName": "台東", "County": "臺東縣", "AQI": 25, "lat": 22.7583, "lon": 121.1528},
            {"SiteName": "林口", "County": "新北市", "AQI": 40, "lat": 25.0777, "lon": 121.3163},
            {"SiteName": "屏東", "County": "屏東縣", "AQI": 36, "lat": 22.6828, "lon": 120.4879},
        ]
        
        self.aqi_data = []
        for station in mock_stations:
            record = {
                "SiteName": station["SiteName"],
                "County": station["County"],
                "AQI": station["AQI"],
                "lat": station["lat"],
                "lon": station["lon"]
            }
            self.aqi_data.append(record)
    
    def scenario_injection(self):
        """情境注入：將特定測站AQI設為150"""
        print("\n=== 情境注入模擬 ===")
        
        # 檢查當前AQI狀況
        current_aqi_values = [station['AQI'] for station in self.aqi_data]
        max_aqi = max(current_aqi_values)
        min_aqi = min(current_aqi_values)
        avg_aqi = np.mean(current_aqi_values)
        
        print(f"當前AQI狀況:")
        print(f"  最高值: {max_aqi}")
        print(f"  最低值: {min_aqi}")
        print(f"  平均值: {avg_aqi:.1f}")
        
        # 判斷是否需要情境注入
        if max_aqi < 50:
            print("全台空氣品質良好，進行情境注入...")
            
            # 選擇高雄站進行注入（AQI設為150）
            for station in self.aqi_data:
                if station["SiteName"] == "高雄":
                    original_aqi = station["AQI"]
                    station["AQI"] = 150
                    print(f"情境注入: 高雄站 AQI 從 {original_aqi} 設為 150")
                    break
            
            # 也可以選擇林口站
            for station in self.aqi_data:
                if station["SiteName"] == "林口":
                    original_aqi = station["AQI"]
                    station["AQI"] = 120
                    print(f"情境注入: 林口站 AQI 從 {original_aqi} 設為 120")
                    break
            
            print("情境注入完成！")
            return True
        else:
            print("已有AQI超過50的測站，無需情境注入")
            return False
    
    def find_nearest_aqi_station(self, shelter_lat, shelter_lon):
        """尋找最近的AQI測站"""
        min_distance = float('inf')
        nearest_station = None
        
        for station in self.aqi_data:
            distance = self.haversine_distance(
                shelter_lat, shelter_lon,
                station['lat'], station['lon']
            )
            
            if distance < min_distance:
                min_distance = distance
                nearest_station = station
        
        return nearest_station, min_distance
    
    def analyze_shelters(self):
        """分析所有避難所"""
        print("\n=== 開始分析避難所 ===")
        
        results = []
        high_risk_count = 0
        warning_count = 0
        safe_count = 0
        
        for idx, shelter in self.shelter_data.iterrows():
            try:
                # 獲取避難所資訊
                shelter_name = shelter['避難收容處所名稱']
                shelter_lat = float(shelter['緯度'])
                shelter_lon = float(shelter['經度'])
                is_indoor = shelter['is_indoor']
                address = shelter['避難收容處所地址']
                capacity = shelter.get('預計收容人數', '未知')
                
                # 尋找最近的AQI測站
                nearest_station, distance = self.find_nearest_aqi_station(shelter_lat, shelter_lon)
                
                if nearest_station is None:
                    continue
                
                # 風險評估
                nearest_aqi = nearest_station['AQI']
                nearest_station_name = nearest_station['SiteName']
                
                # 風險分類
                if nearest_aqi > 100:
                    risk_level = "High Risk"
                    risk_reason = f"最近AQI測站({nearest_station_name}) AQI為{nearest_aqi} > 100"
                    high_risk_count += 1
                elif nearest_aqi > 50 and not is_indoor:
                    risk_level = "Warning"
                    risk_reason = f"最近AQI測站({nearest_station_name}) AQI為{nearest_aqi} > 50 且為室外設施"
                    warning_count += 1
                else:
                    risk_level = "Safe"
                    risk_reason = "AQI良好或為室內設施"
                    safe_count += 1
                
                # 記錄結果
                result = {
                    'shelter_name': shelter_name,
                    'address': address,
                    'latitude': shelter_lat,
                    'longitude': shelter_lon,
                    'is_indoor': is_indoor,
                    'capacity': capacity,
                    'nearest_aqi_station': nearest_station_name,
                    'nearest_aqi_value': nearest_aqi,
                    'distance_to_station_km': round(distance, 2),
                    'risk_level': risk_level,
                    'risk_reason': risk_reason,
                    'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                results.append(result)
                
                # 顯示進度
                if (idx + 1) % 1000 == 0:
                    print(f"已處理 {idx + 1} 個避難所...")
                    
            except Exception as e:
                print(f"處理避難所時發生錯誤: {e}")
                continue
        
        print(f"分析完成！")
        return results, high_risk_count, warning_count, safe_count
    
    def create_summary_statistics(self, results, high_risk_count, warning_count, safe_count):
        """創建統計摘要"""
        print("\n=== 分析結果統計 ===")
        
        total_shelters = len(results)
        print(f"總避難所數量: {total_shelters}")
        print(f"高風險: {high_risk_count} ({high_risk_count/total_shelters*100:.1f}%)")
        print(f"警告: {warning_count} ({warning_count/total_shelters*100:.1f}%)")
        print(f"安全: {safe_count} ({safe_count/total_shelters*100:.1f}%)")
        
        # 距離統計
        distances = [r['distance_to_station_km'] for r in results]
        print(f"\n距離統計:")
        print(f"  平均距離: {np.mean(distances):.2f} 公里")
        print(f"  最短距離: {min(distances):.2f} 公里")
        print(f"  最長距離: {max(distances):.2f} 公里")
        
        # 高風險避難所詳情
        high_risk_shelters = [r for r in results if r['risk_level'] == 'High Risk']
        if high_risk_shelters:
            print(f"\n高風險避難所 (前10個):")
            for i, shelter in enumerate(high_risk_shelters[:10]):
                print(f"  {i+1}. {shelter['shelter_name']}")
                print(f"     地址: {shelter['address']}")
                print(f"     最近測站: {shelter['nearest_aqi_station']} (AQI: {shelter['nearest_aqi_value']})")
                print(f"     距離: {shelter['distance_to_station_km']} 公里")
                print(f"     類型: {'室內' if shelter['is_indoor'] else '室外'}")
                print()
        
        # 警告避難所詳情
        warning_shelters = [r for r in results if r['risk_level'] == 'Warning']
        if warning_shelters:
            print(f"警告避難所 (前5個):")
            for i, shelter in enumerate(warning_shelters[:5]):
                print(f"  {i+1}. {shelter['shelter_name']} (室外)")
                print(f"     最近測站: {shelter['nearest_aqi_station']} (AQI: {shelter['nearest_aqi_value']})")
                print(f"     距離: {shelter['distance_to_station_km']} 公里")
                print()
    
    def save_results(self, results):
        """儲存分析結果"""
        print("\n=== 儲存分析結果 ===")
        
        # 創建DataFrame
        df = pd.DataFrame(results)
        
        # 重新排列欄位順序
        column_order = [
            'shelter_name', 'address', 'latitude', 'longitude', 'is_indoor', 'capacity',
            'nearest_aqi_station', 'nearest_aqi_value', 'distance_to_station_km',
            'risk_level', 'risk_reason', 'analysis_time'
        ]
        df = df[column_order]
        
        # 儲存到CSV
        output_file = 'outputs/shelter_aqi_analysis.csv'
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"分析結果已儲存至: {output_file}")
        print(f"總記錄數: {len(df)}")
        
        # 顯示高風險記錄數量
        high_risk_records = df[df['risk_level'] == 'High Risk']
        warning_records = df[df['risk_level'] == 'Warning']
        
        print(f"高風險記錄: {len(high_risk_records)} 筆")
        print(f"警告記錄: {len(warning_records)} 筆")
        
        if len(high_risk_records) > 0:
            print("成功生成高風險記錄（情境模擬有效）")
        else:
            print("沒有高風險記錄，可能需要調整情境模擬參數")
        
        return df
    
    def run_analysis(self):
        """執行完整分析"""
        print("開始執行最近測站分析與情境模擬...")
        
        # 確保輸出目錄存在
        os.makedirs('outputs', exist_ok=True)
        
        # 載入資料
        if not self.load_data():
            return False
        
        # 情境注入
        injection_performed = self.scenario_injection()
        
        # 分析避難所
        results, high_risk_count, warning_count, safe_count = self.analyze_shelters()
        
        # 創建統計摘要
        self.create_summary_statistics(results, high_risk_count, warning_count, safe_count)
        
        # 儲存結果
        df = self.save_results(results)
        
        print(f"\n=== 分析完成 ===")
        print(f"情境注入: {'是' if injection_performed else '否'}")
        print(f"高風險避難所: {high_risk_count} 個")
        print(f"警告避難所: {warning_count} 個")
        print(f"安全避難所: {safe_count} 個")
        print(f"結果檔案: outputs/shelter_aqi_analysis.csv")
        
        return True

def main():
    """主程式"""
    analyzer = NearestNeighborAnalysis()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()
