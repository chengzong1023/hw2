#!/usr/bin/env python3
"""
Spatial Overlay: AQI 測站 + 避難所疊圖
使用Folium創建完整的空間疊圖分析
"""

import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
import os
from datetime import datetime

class SpatialOverlayMap:
    def __init__(self):
        self.aqi_data = None
        self.shelter_data = None
        self.taiwan_center = [23.8, 120.9]
        
    def create_mock_aqi_data(self):
        """創建模擬AQI資料"""
        stations = [
            {"name": "台北", "county": "臺北市", "lat": 25.0173, "lon": 121.5395, "aqi": 45},
            {"name": "新北", "county": "新北市", "lat": 25.0167, "lon": 121.4667, "aqi": 52},
            {"name": "桃園", "county": "桃園市", "lat": 24.9936, "lon": 121.3010, "aqi": 38},
            {"name": "台中", "county": "臺中市", "lat": 24.1477, "lon": 120.6736, "aqi": 67},
            {"name": "台南", "county": "臺南市", "lat": 22.9999, "lon": 120.2269, "aqi": 41},
            {"name": "高雄", "county": "高雄市", "lat": 22.6273, "lon": 120.3014, "aqi": 150},
            {"name": "基隆", "county": "基隆市", "lat": 25.1276, "lon": 121.7392, "aqi": 35},
            {"name": "新竹", "county": "新竹市", "lat": 24.8138, "lon": 120.9675, "aqi": 42},
            {"name": "嘉義", "county": "嘉義市", "lat": 23.4801, "lon": 120.4491, "aqi": 48},
            {"name": "宜蘭", "county": "宜蘭縣", "lat": 24.6929, "lon": 121.7705, "aqi": 33},
            {"name": "花蓮", "county": "花蓮縣", "lat": 23.7519, "lon": 121.6067, "aqi": 28},
            {"name": "台東", "county": "臺東縣", "lat": 22.7583, "lon": 121.1528, "aqi": 25},
            {"name": "林口", "county": "新北市", "lat": 25.0777, "lon": 121.3163, "aqi": 120},
            {"name": "板橋", "county": "新北市", "lat": 25.0129, "lon": 121.4647, "aqi": 58},
            {"name": "三重", "county": "新北市", "lat": 25.0667, "lon": 121.4833, "aqi": 62}
        ]
        return pd.DataFrame(stations)
    
    def load_shelter_data(self):
        """載入避難所資料"""
        try:
            df = pd.read_csv('data/shelters_cleaned.csv', encoding='utf-8-sig')
            
            # 根據室內/室外欄位創建is_indoor欄位
            def classify_shelter(row):
                if pd.notna(row['室內']) and row['室內'] == '是':
                    return True
                elif pd.notna(row['室外']) and row['室外'] == '是':
                    return False
                else:
                    # 如果都沒有標記，根據名稱推斷
                    name = str(row['避難收容處所名稱']).lower()
                    indoor_keywords = ['活動中心', '禮堂', '體育館', '學校', '社區中心', '辦公處']
                    outdoor_keywords = ['公園', '廣場', '體育場', '停車場']
                    
                    for keyword in indoor_keywords:
                        if keyword in name:
                            return True
                    for keyword in outdoor_keywords:
                        if keyword in name:
                            return False
                    
                    # 預設為室內
                    return True
            
            df['is_indoor'] = df.apply(classify_shelter, axis=1)
            return df
            
        except Exception as e:
            print(f"載入避難所資料失敗: {e}")
            # 如果載入失敗，創建模擬資料
            shelters = []
            indoor_places = ["活動中心", "禮堂", "體育館", "學校", "社區中心"]
            outdoor_places = ["公園", "廣場", "體育場", "停車場"]
            
            for i in range(100):  # 創建100個模擬避難所
                import random
                lat = 22.0 + random.random() * 4.0
                lon = 119.0 + random.random() * 4.0
                place_type = random.choice(indoor_places + outdoor_places)
                is_indoor = place_type in indoor_places
                
                shelters.append({
                    "避難收容處所名稱": f"{place_type}{i+1}",
                    "緯度": lat,
                    "經度": lon,
                    "is_indoor": is_indoor,
                    "避難收容處所地址": f"台灣某地址{i+1}號",
                    "預計收容人數": random.randint(100, 1000)
                })
            
            return pd.DataFrame(shelters)
    
    def get_aqi_color(self, aqi):
        """根據AQI值獲取顏色"""
        if aqi <= 50:
            return 'green'
        elif aqi <= 100:
            return 'yellow'
        elif aqi <= 150:
            return 'orange'
        elif aqi <= 200:
            return 'red'
        elif aqi <= 300:
            return 'purple'
        else:
            return 'maroon'
    
    def get_aqi_level(self, aqi):
        """根據AQI值獲取等級描述"""
        if aqi <= 50:
            return '良好'
        elif aqi <= 100:
            return '普通'
        elif aqi <= 150:
            return '對敏感族群不健康'
        elif aqi <= 200:
            return '對所有族群不健康'
        elif aqi <= 300:
            return '非常不健康'
        else:
            return '危害'
    
    def create_map(self):
        """創建空間疊圖地圖"""
        print("正在創建Spatial Overlay地圖...")
        
        # 載入資料
        self.aqi_data = self.create_mock_aqi_data()
        self.shelter_data = self.load_shelter_data()
        
        print(f"AQI測站數量: {len(self.aqi_data)}")
        print(f"避難所數量: {len(self.shelter_data)}")
        
        # 創建基礎地圖
        m = folium.Map(
            location=self.taiwan_center,
            zoom_start=7,
            tiles='OpenStreetMap'
        )
        
        # 添加AQI測站圖層
        aqi_group = folium.FeatureGroup(name='AQI 測站')
        
        for _, station in self.aqi_data.iterrows():
            color = self.get_aqi_color(station['aqi'])
            level = self.get_aqi_level(station['aqi'])
            
            popup_content = f"""
            <b>{station['name']}</b><br>
            縣市: {station['county']}<br>
            AQI: {station['aqi']}<br>
            等級: {level}<br>
            <small>更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}</small>
            """
            
            folium.CircleMarker(
                location=[station['lat'], station['lon']],
                radius=8,
                popup=folium.Popup(popup_content, max_width=300),
                color='black',
                weight=2,
                fillColor=color,
                fillOpacity=0.8,
                tooltip=f"{station['name']}: AQI {station['aqi']}"
            ).add_to(aqi_group)
        
        aqi_group.add_to(m)
        
        # 添加避難所圖層
        indoor_group = folium.FeatureGroup(name='室內避難所')
        outdoor_group = folium.FeatureGroup(name='室外避難所')
        
        indoor_count = 0
        outdoor_count = 0
        
        for _, shelter in self.shelter_data.iterrows():
            try:
                lat = float(shelter['緯度'])
                lon = float(shelter['經度'])
                is_indoor = shelter['is_indoor']
                name = shelter['避難收容處所名稱']
                address = shelter.get('避難收容處所地址', '未知地址')
                capacity = shelter.get('預計收容人數', '未知')
                
                popup_content = f"""
                <b>{name}</b><br>
                地址: {address}<br>
                類型: {'室內' if is_indoor else '室外'}<br>
                收容人數: {capacity}<br>
                <small>坐標: ({lat:.6f}, {lon:.6f})</small>
                """
                
                if is_indoor:
                    icon = folium.Icon(color='blue', icon='home', prefix='fa')
                    indoor_count += 1
                    target_group = indoor_group
                else:
                    icon = folium.Icon(color='green', icon='tree', prefix='fa')
                    outdoor_count += 1
                    target_group = outdoor_group
                
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_content, max_width=300),
                    icon=icon,
                    tooltip=f"{name} ({'室內' if is_indoor else '室外'})"
                ).add_to(target_group)
                
            except Exception as e:
                continue
        
        indoor_group.add_to(m)
        outdoor_group.add_to(m)
        
        # 添加AQI熱力圖
        heat_data = []
        for _, station in self.aqi_data.iterrows():
            heat_data.append([station['lat'], station['lon'], float(station['aqi'])])
        
        if heat_data:
            heatmap_group = folium.FeatureGroup(name='AQI 熱力圖')
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
        
        # 添加圖例
        legend_html = '''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 220px; height: 320px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:12px; padding: 10px">
        <h4>Spatial Overlay 圖例</h4>
        <b>AQI 測站</b><br>
        <i class="fa fa-circle" style="color:green"></i> 良好 (0-50)<br>
        <i class="fa fa-circle" style="color:yellow"></i> 普通 (51-100)<br>
        <i class="fa fa-circle" style="color:orange"></i> 對敏感族群不健康 (101-150)<br>
        <i class="fa fa-circle" style="color:red"></i> 對所有族群不健康 (151-200)<br>
        <i class="fa fa-circle" style="color:purple"></i> 非常不健康 (201-300)<br>
        <i class="fa fa-circle" style="color:maroon"></i> 危害 (301+)<br><br>
        <b>避難所</b><br>
        <i class="fa fa-home" style="color:blue"></i> 室內避難所<br>
        <i class="fa fa-tree" style="color:green"></i> 室外避難所<br><br>
        <b>圖層</b><br>
        🔵 AQI 測站<br>
        🏠 室內避難所<br>
        🌳 室外避難所<br>
        🔥 AQI 熱力圖<br>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # 添加圖層控制
        folium.LayerControl().add_to(m)
        
        # 添加全屏功能
        from folium.plugins import Fullscreen
        Fullscreen().add_to(m)
        
        # 儲存地圖
        output_file = 'outputs/spatial_overlay_map.html'
        m.save(output_file)
        
        print(f"地圖已儲存至: {output_file}")
        print(f"統計: 室內避難所 {indoor_count} 個, 室外避難所 {outdoor_count} 個")
        
        return output_file, indoor_count, outdoor_count

def main():
    """主程式"""
    print("=== Spatial Overlay: AQI 測站 + 避難所疊圖 ===")
    
    # 確保輸出目錄存在
    os.makedirs('outputs', exist_ok=True)
    
    # 創建地圖
    map_creator = SpatialOverlayMap()
    output_file, indoor_count, outdoor_count = map_creator.create_map()
    
    print(f"\nSpatial Overlay地圖創建完成！")
    print(f"檔案位置: {output_file}")
    print(f"室內避難所: {indoor_count} 個")
    print(f"室外避難所: {outdoor_count} 個")
    print(f"請用瀏覽器開啟查看完整的地圖和互動功能")

if __name__ == "__main__":
    main()
