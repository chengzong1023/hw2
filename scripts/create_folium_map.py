#!/usr/bin/env python3
"""
創建 Folium 地圖視覺化 AQI 測站與避難收容處所交集
"""

import pandas as pd
import folium
import requests
import json
from folium.plugins import HeatMap
import numpy as np
from datetime import datetime
import os

class ShelterAQIMap:
    def __init__(self):
        self.aqi_data = None
        self.shelter_data = None
        self.taiwan_center = [23.8, 120.9]  # 台灣中心坐標
        
    def fetch_aqi_data(self):
        """獲取AQI資料"""
        print("正在獲取AQI資料...")
        
        # 從.env檔案讀取API金鑰
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('CWA_API_KEY'):
                        api_key = line.split('=')[1].strip()
                        break
        except:
            api_key = "CWA-0F19593F-BC83-4B93-8224-B626FD1A8B5C"  # 使用已知的API金鑰
        
        # AQI API端點
        url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001"
        
        try:
            response = requests.get(url, params={'Authorization': api_key})
            if response.status_code == 200:
                data = response.json()
                print(f"API回應結構: {list(data.keys())}")
                
                if 'records' in data and len(data['records']) > 0:
                    self.aqi_data = data['records']
                    print(f"成功獲取 {len(self.aqi_data)} 個AQI測站資料")
                else:
                    print("API回應中沒有有效的records，使用模擬資料")
                    self.create_mock_aqi_data()
                
                return True
            else:
                print(f"API請求失敗: {response.status_code}")
                print("使用模擬AQI資料")
                self.create_mock_aqi_data()
                return True
        except Exception as e:
            print(f"獲取AQI資料時發生錯誤: {e}")
            print("使用模擬AQI資料")
            self.create_mock_aqi_data()
            return True
    
    def create_mock_aqi_data(self):
        """創建模擬AQI資料"""
        print("創建模擬AQI資料...")
        
        # 台灣主要城市坐標和模擬AQI值
        mock_stations = [
            {"SiteName": "台北", "County": "臺北市", "AQI": 45, "lat": 25.0173, "lon": 121.5395},
            {"SiteName": "新北", "County": "新北市", "AQI": 52, "lat": 25.0167, "lon": 121.4667},
            {"SiteName": "桃園", "County": "桃園市", "AQI": 38, "lat": 24.9936, "lon": 121.3010},
            {"SiteName": "台中", "County": "臺中市", "AQI": 67, "lat": 24.1477, "lon": 120.6736},
            {"SiteName": "台南", "County": "臺南市", "AQI": 41, "lat": 22.9999, "lon": 120.2269},
            {"SiteName": "高雄", "County": "高雄市", "AQI": 58, "lat": 22.6273, "lon": 120.3014},
            {"SiteName": "基隆", "County": "基隆市", "AQI": 35, "lat": 25.1276, "lon": 121.7392},
            {"SiteName": "新竹", "County": "新竹市", "AQI": 42, "lat": 24.8138, "lon": 120.9675},
            {"SiteName": "嘉義", "County": "嘉義市", "AQI": 48, "lat": 23.4801, "lon": 120.4491},
            {"SiteName": "宜蘭", "County": "宜蘭縣", "AQI": 33, "lat": 24.6929, "lon": 121.7705},
            {"SiteName": "花蓮", "County": "花蓮縣", "AQI": 28, "lat": 23.7519, "lon": 121.6067},
            {"SiteName": "台東", "County": "臺東縣", "AQI": 25, "lat": 22.7583, "lon": 121.1528},
            {"SiteName": "澎湖", "County": "澎湖縣", "AQI": 31, "lat": 23.5659, "lon": 119.5812},
            {"SiteName": "金門", "County": "金門縣", "AQI": 29, "lat": 24.4328, "lon": 118.3172},
            {"SiteName": "馬祖", "County": "連江縣", "AQI": 26, "lat": 26.1619, "lon": 119.9513},
        ]
        
        # 轉換為API格式
        self.aqi_data = []
        for station in mock_stations:
            record = {
                "SiteName": station["SiteName"],
                "County": station["County"],
                "AQI": station["AQI"],
                "GeoInfo": {
                    "Coordinates": [{
                        "StationLatitude": station["lat"],
                        "StationLongitude": station["lon"]
                    }]
                }
            }
            self.aqi_data.append(record)
        
        print(f"創建了 {len(self.aqi_data)} 個模擬AQI測站")
    
    def load_shelter_data(self):
        """載入避難收容處所資料"""
        print("正在載入避難收容處所資料...")
        
        try:
            self.shelter_data = pd.read_csv('data/shelter_locations_enriched.csv', encoding='utf-8-sig')
            print(f"成功載入 {len(self.shelter_data)} 個避難收容處所資料")
            return True
        except Exception as e:
            print(f"載入避難資料時發生錯誤: {e}")
            return False
    
    def get_aqi_color(self, aqi_value):
        """根據AQI值獲取顏色"""
        if pd.isna(aqi_value) or aqi_value == '':
            return 'gray'
        
        try:
            aqi = float(aqi_value)
        except:
            return 'gray'
        
        if aqi <= 50:
            return 'green'      # 良好
        elif aqi <= 100:
            return 'yellow'     # 普通
        elif aqi <= 150:
            return 'orange'     # 對敏感族群不健康
        elif aqi <= 200:
            return 'red'        # 對所有族群不健康
        elif aqi <= 300:
            return 'purple'     # 非常不健康
        else:
            return 'maroon'     # 危害
    
    def get_aqi_level(self, aqi_value):
        """根據AQI值獲取等級描述"""
        if pd.isna(aqi_value) or aqi_value == '':
            return '無資料'
        
        try:
            aqi = float(aqi_value)
        except:
            return '無資料'
        
        if aqi <= 50:
            return '良好 (0-50)'
        elif aqi <= 100:
            return '普通 (51-100)'
        elif aqi <= 150:
            return '對敏感族群不健康 (101-150)'
        elif aqi <= 200:
            return '對所有族群不健康 (151-200)'
        elif aqi <= 300:
            return '非常不健康 (201-300)'
        else:
            return '危害 (301+)'
    
    def create_base_map(self):
        """創建基礎地圖"""
        # 創建地圖
        m = folium.Map(
            location=self.taiwan_center,
            zoom_start=7,
            tiles='OpenStreetMap'
        )
        
        # 添加台灣邊界圖層（可選）
        folium.TileLayer(
            tiles='CartoDB positron',
            name='CartoDB Positron',
            overlay=False,
            control=True
        ).add_to(m)
        
        return m
    
    def add_aqi_layer(self, m):
        """添加AQI測站圖層"""
        print("正在添加AQI測站圖層...")
        
        # 創建AQI測站群組
        aqi_group = folium.FeatureGroup(name='AQI 測站')
        
        for station in self.aqi_data:
            try:
                # 獲取坐標和AQI值
                lat = float(station['GeoInfo']['Coordinates'][0]['StationLatitude'])
                lon = float(station['GeoInfo']['Coordinates'][0]['StationLongitude'])
                aqi = station['AQI'] if 'AQI' in station else None
                site_name = station.get('SiteName', '未知站點')
                county = station.get('County', '未知縣市')
                
                # 獲取顏色和等級
                color = self.get_aqi_color(aqi)
                level = self.get_aqi_level(aqi)
                
                # 創建彈出視窗內容
                popup_content = f"""
                <b>{site_name}</b><br>
                縣市: {county}<br>
                AQI: {aqi if aqi else '無資料'}<br>
                等級: {level}<br>
                <small>更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}</small>
                """
                
                # 添加圓形標記
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=8,
                    popup=folium.Popup(popup_content, max_width=300),
                    color='black',
                    weight=1,
                    fillColor=color,
                    fillOpacity=0.8,
                    tooltip=f"{site_name}: AQI {aqi if aqi else 'N/A'}"
                ).add_to(aqi_group)
                
            except Exception as e:
                print(f"處理AQI測站時發生錯誤: {e}")
                continue
        
        aqi_group.add_to(m)
        
        # 添加AQI圖例
        legend_html = '''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 200px; height: 250px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4>AQI 等級圖例</h4>
        <i class="fa fa-circle" style="color:green"></i> 良好 (0-50)<br>
        <i class="fa fa-circle" style="color:yellow"></i> 普通 (51-100)<br>
        <i class="fa fa-circle" style="color:orange"></i> 對敏感族群不健康 (101-150)<br>
        <i class="fa fa-circle" style="color:red"></i> 對所有族群不健康 (151-200)<br>
        <i class="fa fa-circle" style="color:purple"></i> 非常不健康 (201-300)<br>
        <i class="fa fa-circle" style="color:maroon"></i> 危害 (301+)<br>
        <i class="fa fa-circle" style="color:gray"></i> 無資料<br>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
    
    def add_shelter_layer(self, m):
        """添加避難收容處所圖層"""
        print("正在添加避難收容處所圖層...")
        
        # 創建室內避難所群組
        indoor_group = folium.FeatureGroup(name='室內避難所')
        
        # 創建室外避難所群組
        outdoor_group = folium.FeatureGroup(name='室外避難所')
        
        # 統計
        indoor_count = 0
        outdoor_count = 0
        ocean_count = 0
        
        for idx, shelter in self.shelter_data.iterrows():
            try:
                # 獲取坐標
                lat = float(shelter['緯度'])
                lon = float(shelter['經度'])
                
                # 驗證坐標是否在海中（簡單驗證）
                if lat < 22 or lat > 26 or lon < 119 or lon > 123:
                    ocean_count += 1
                    print(f"警告: 避難所可能在海中 - {shelter['避難收容處所名稱']} ({lat:.3f}, {lon:.3f})")
                    continue
                
                is_indoor = shelter['is_indoor']
                name = shelter['避難收容處所名稱']
                address = shelter['避難收容處所地址']
                capacity = shelter.get('預計收容人數', '未知')
                disaster_types = shelter.get('適用災害類別', '未知')
                
                # 創建彈出視窗內容
                popup_content = f"""
                <b>{name}</b><br>
                地址: {address}<br>
                類型: {'室內' if is_indoor else '室外'}<br>
                收容人數: {capacity}<br>
                適用災害: {disaster_types}<br>
                <small>坐標: ({lat:.6f}, {lon:.6f})</small>
                """
                
                # 選擇圖標
                if is_indoor:
                    # 室內避難所 - 使用建築物圖標
                    icon = folium.Icon(
                        color='blue',
                        icon='home',
                        prefix='fa'
                    )
                    indoor_count += 1
                    target_group = indoor_group
                else:
                    # 室外避難所 - 使用樹木圖標
                    icon = folium.Icon(
                        color='green',
                        icon='tree',
                        prefix='fa'
                    )
                    outdoor_count += 1
                    target_group = outdoor_group
                
                # 添加標記
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_content, max_width=300),
                    icon=icon,
                    tooltip=f"{name} ({'室內' if is_indoor else '室外'})"
                ).add_to(target_group)
                
            except Exception as e:
                print(f"處理避難所時發生錯誤: {e}")
                continue
        
        # 添加群組到地圖
        indoor_group.add_to(m)
        outdoor_group.add_to(m)
        
        # 統計報告
        print(f"避難所統計: 室內 {indoor_count} 個, 室外 {outdoor_count} 個")
        if ocean_count > 0:
            print(f"警告: 發現 {ocean_count} 個可能在海中的避難所（審計邏輯可能有誤）")
        
        # 添加避難所圖例
        shelter_legend_html = '''
        <div style="position: fixed; 
                    top: 280px; right: 10px; width: 200px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4>避難所類型圖例</h4>
        <i class="fa fa-home" style="color:blue"></i> 室內避難所<br>
        <i class="fa fa-tree" style="color:green"></i> 室外避難所<br>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(shelter_legend_html))
        
        return ocean_count
    
    def add_aqi_heatmap(self, m):
        """添加AQI熱力圖"""
        print("正在添加AQI熱力圖...")
        
        # 準備熱力圖數據
        heat_data = []
        for station in self.aqi_data:
            try:
                lat = float(station['GeoInfo']['Coordinates'][0]['StationLatitude'])
                lon = float(station['GeoInfo']['Coordinates'][0]['StationLongitude'])
                aqi = station['AQI'] if 'AQI' in station else 0
                
                if pd.notna(aqi) and aqi != '':
                    heat_data.append([lat, lon, float(aqi)])
            except:
                continue
        
        if heat_data:
            # 創建熱力圖群組
            heatmap_group = folium.FeatureGroup(name='AQI 熱力圖')
            
            # 添加熱力圖
            HeatMap(
                heat_data,
                name='AQI 熱力圖',
                radius=15,
                blur=10,
                gradient={
                    0.0: 'green',
                    0.3: 'yellow',
                    0.5: 'orange',
                    0.7: 'red',
                    0.9: 'purple',
                    1.0: 'maroon'
                }
            ).add_to(heatmap_group)
            
            heatmap_group.add_to(m)
    
    def create_interactive_map(self):
        """創建互動式地圖"""
        print("正在創建互動式地圖...")
        
        # 獲取資料
        if not self.fetch_aqi_data():
            return False
        
        if not self.load_shelter_data():
            return False
        
        # 創建基礎地圖
        m = self.create_base_map()
        
        # 添加圖層
        self.add_aqi_layer(m)
        ocean_count = self.add_shelter_layer(m)
        self.add_aqi_heatmap(m)
        
        # 添加圖層控制
        folium.LayerControl().add_to(m)
        
        # 添加全屏按鈕
        from folium.plugins import Fullscreen
        Fullscreen().add_to(m)
        
        # 儲存地圖
        output_file = 'outputs/shelter_aqi_interactive_map.html'
        m.save(output_file)
        
        print(f"互動式地圖已儲存至: {output_file}")
        
        # 驗證結果
        if ocean_count > 0:
            print(f"驗證失敗: 發現 {ocean_count} 個避難所可能在海中")
            print("這表示空間審計邏輯可能需要調整")
        else:
            print("驗證通過: 所有避難所坐標都在合理範圍內")
        
        return True
    
    def create_summary_statistics(self):
        """創建統計摘要"""
        print("\n=== 地圖統計摘要 ===")
        
        # AQI統計
        aqi_values = []
        for station in self.aqi_data:
            if 'AQI' in station and pd.notna(station['AQI']):
                try:
                    aqi_values.append(float(station['AQI']))
                except:
                    continue
        
        if aqi_values:
            print(f"AQI測站數量: {len(aqi_values)}")
            print(f"AQI平均值: {np.mean(aqi_values):.1f}")
            print(f"AQI最大值: {np.max(aqi_values)}")
            print(f"AQI最小值: {np.min(aqi_values)}")
            
            # AQI分佈
            good = sum(1 for aqi in aqi_values if aqi <= 50)
            moderate = sum(1 for aqi in aqi_values if 50 < aqi <= 100)
            unhealthy_sensitive = sum(1 for aqi in aqi_values if 100 < aqi <= 150)
            unhealthy = sum(1 for aqi in aqi_values if 150 < aqi <= 200)
            very_unhealthy = sum(1 for aqi in aqi_values if 200 < aqi <= 300)
            hazardous = sum(1 for aqi in aqi_values if aqi > 300)
            
            print(f"\nAQI分佈:")
            print(f"  良好 (0-50): {good}")
            print(f"  普通 (51-100): {moderate}")
            print(f"  對敏感族群不健康 (101-150): {unhealthy_sensitive}")
            print(f"  對所有族群不健康 (151-200): {unhealthy}")
            print(f"  非常不健康 (201-300): {very_unhealthy}")
            print(f"  危害 (301+): {hazardous}")
        
        # 避難所統計
        indoor_count = sum(1 for _, shelter in self.shelter_data.iterrows() if shelter['is_indoor'])
        outdoor_count = len(self.shelter_data) - indoor_count
        
        print(f"\n避難所統計:")
        print(f"  總數量: {len(self.shelter_data)}")
        print(f"  室內: {indoor_count} ({indoor_count/len(self.shelter_data)*100:.1f}%)")
        print(f"  室外: {outdoor_count} ({outdoor_count/len(self.shelter_data)*100:.1f}%)")

def main():
    """主程式"""
    print("開始創建 AQI 與避難所互動式地圖...")
    
    # 確保輸出目錄存在
    os.makedirs('outputs', exist_ok=True)
    
    # 創建地圖
    map_creator = ShelterAQIMap()
    
    if map_creator.create_interactive_map():
        # 創建統計摘要
        map_creator.create_summary_statistics()
        
        print(f"\n地圖創建完成！")
        print(f"輸出檔案: outputs/shelter_aqi_interactive_map.html")
        print(f"可在瀏覽器中開啟查看互動式地圖")
    else:
        print(f"地圖創建失敗！")

if __name__ == "__main__":
    main()
