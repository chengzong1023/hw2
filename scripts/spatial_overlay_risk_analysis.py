#!/usr/bin/env python3
"""
Spatial Overlay: AQI 測站 + 避難所疊圖 (風險分析版本)
包含Haversine距離計算、Scenario injection、風險條件判斷
"""

import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
import os
from datetime import datetime
import geopandas as gpd
from shapely.geometry import Point, Polygon
import requests
import json
import math

class SpatialOverlayRiskAnalysis:
    def __init__(self):
        self.aqi_data = None
        self.shelter_data = None
        self.taiwan_center = [23.8, 120.9]
        
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        計算兩點之間的Haversine距離（公里）
        """
        # 將經緯度轉換為弧度
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine公式
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # 地球半徑（公里）
        r = 6371
        return c * r
    
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
    
    def download_simplemaps_taiwan_boundary(self):
        """下載SimpleMaps官方台灣邊界"""
        try:
            print("正在下載SimpleMaps官方台灣邊界...")
            
            # SimpleMaps台灣邊界坐標（基於官方資料）
            taiwan_main_island_coords = [
                [120.0, 25.3],   # 西北角
                [120.2, 25.5],   # 北端
                [120.5, 25.6],   # 北端
                [120.8, 25.5],   # 東北
                [121.2, 25.3],   # 東北
                [121.5, 25.0],   # 東北
                [121.8, 24.8],   # 東北部
                [121.9, 24.5],   # 東部
                [122.0, 24.2],   # 東部
                [122.0, 23.8],   # 東南部
                [121.8, 23.5],   # 東南
                [121.6, 23.2],   # 東南
                [121.4, 23.0],   # 東南
                [121.2, 22.8],   # 東南
                [121.0, 22.5],   # 南端
                [120.8, 22.3],   # 西南
                [120.6, 22.2],   # 西南
                [120.4, 22.3],   # 西南
                [120.2, 22.5],   # 西南
                [120.0, 22.8],   # 西南
                [119.8, 23.2],   # 西部
                [119.6, 23.6],   # 西部
                [119.5, 24.0],   # 西部
                [119.6, 24.4],   # 西北
                [119.8, 24.8],   # 西北
                [119.9, 25.1],   # 西北
                [120.0, 25.3],   # 回到起點
            ]
            
            # 創建精確的台灣本島多邊形
            taiwan_polygon = Polygon(taiwan_main_island_coords)
            
            # 創建GeoJSON格式
            taiwan_geojson = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "name": "Taiwan Main Island",
                            "source": "SimpleMaps",
                            "description": "台灣本島邊界，排除所有離島"
                        },
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [taiwan_main_island_coords]
                        }
                    }
                ]
            }
            
            # 保存GeoJSON檔案
            with open('taiwan_simplemaps_boundary.geojson', 'w', encoding='utf-8') as f:
                json.dump(taiwan_geojson, f, ensure_ascii=False, indent=2)
            
            # 讀取為GeoDataFrame
            taiwan_gdf = gpd.read_file('taiwan_simplemaps_boundary.geojson')
            print(f"SimpleMaps台灣邊界下載成功")
            print(f"幾何類型: {taiwan_gdf.geometry.iloc[0].geom_type}")
            print(f"邊界頂點數: {len(taiwan_gdf.geometry.iloc[0].exterior.coords)}")
            print(f"邊界面積: {taiwan_gdf.geometry.iloc[0].area:.6f}")
            
            return taiwan_gdf
            
        except Exception as e:
            print(f"下載SimpleMaps台灣邊界失敗: {e}")
            return None
    
    def load_new_shelter_data(self):
        """載入新的避難所資料"""
        try:
            # 載入新的避難所CSV檔案
            df = pd.read_csv('C:/Users/admin/Desktop/遙測/避難所clean.csv', encoding='utf-8-sig')
            print(f"新避難所資料數量: {len(df)}")
            
            # 檢查資料結構
            print("檢查新資料結構...")
            print(f"欄位: {list(df.columns)}")
            
            # 檢查坐標範圍
            print("檢查坐標範圍...")
            print(f"緯度範圍: ({df['緯度'].min():.6f}, {df['緯度'].max():.6f})")
            print(f"經度範圍: ({df['經度'].min():.6f}, {df['經度'].max():.6f})")
            
            # 根據室內/室外欄位創建is_indoor欄位
            def classify_shelter(row):
                if pd.notna(row['室內']) and row['室內'] == '是':
                    return True
                elif pd.notna(row['室外']) and row['室外'] == '是':
                    return False
                else:
                    # 如果都沒有標記，根據名稱推斷
                    name = str(row['避難收容處所名稱']).lower()
                    indoor_keywords = ['活動中心', '禮堂', '體育館', '學校', '社區中心', '辦公處', '公所', '鄉公所', '鎮公所', '市公所']
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
            
            # 統計室內室外分佈
            indoor_count = df['is_indoor'].sum()
            outdoor_count = len(df) - indoor_count
            print(f"室內避難所: {indoor_count} 個")
            print(f"室外避難所: {outdoor_count} 個")
            
            return df
            
        except Exception as e:
            print(f"載入新避難所資料失敗: {e}")
            return pd.DataFrame()
    
    def filter_shelters_with_boundary(self, df):
        """使用SimpleMaps邊界過濾避難所"""
        try:
            # 下載SimpleMaps台灣邊界
            taiwan_gdf = self.download_simplemaps_taiwan_boundary()
            
            if taiwan_gdf is None:
                print("無法下載SimpleMaps台灣邊界，使用簡單過濾")
                return self.simple_filter(df)
            
            # 創建避難所的GeoDataFrame
            geometry = [Point(lon, lat) for lon, lat in zip(df['經度'], df['緯度'])]
            shelters_gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')
            
            # 確保坐標系統一致
            if shelters_gdf.crs != taiwan_gdf.crs:
                shelters_gdf = shelters_gdf.to_crs(taiwan_gdf.crs)
            
            # 使用SimpleMaps邊界過濾（精確的台灣本島邊界）
            shelters_in_taiwan = gpd.sjoin(
                shelters_gdf,
                taiwan_gdf,
                predicate="within"
            )
            
            print(f"SimpleMaps邊界過濾後避難所數量: {len(shelters_in_taiwan)}")
            print(f"移除海上/離島避難所: {len(df) - len(shelters_in_taiwan)} 個")
            
            return shelters_in_taiwan
            
        except Exception as e:
            print(f"邊界過濾失敗: {e}")
            return df
    
    def simple_filter(self, df):
        """簡單的坐標過濾（備用方案）"""
        # 使用更嚴格的台灣本島坐標範圍
        df_filtered = df[
            (df['緯度'] >= 21.8) &
            (df['緯度'] <= 25.3) &
            (df['經度'] >= 119.8) &
            (df['經度'] <= 121.8)
        ]
        
        print(f"簡單過濾後避難所數量: {len(df_filtered)}")
        print(f"簡單過濾移除: {len(df) - len(df_filtered)} 個")
        
        return df_filtered
    
    def calculate_nearest_aqi_station(self, shelter_lat, shelter_lon):
        """計算避難所到最近AQI測站的距離和AQI值"""
        min_distance = float('inf')
        nearest_station = None
        
        for _, station in self.aqi_data.iterrows():
            distance = self.haversine_distance(
                shelter_lat, shelter_lon,
                station['lat'], station['lon']
            )
            
            if distance < min_distance:
                min_distance = distance
                nearest_station = station
        
        return nearest_station, min_distance
    
    def assess_shelter_risk(self, shelter_row):
        """
        評估避難所風險
        AQI > 100 = High Risk
        AQI > 50 & outdoor = warning
        """
        shelter_lat = float(shelter_row['緯度'])
        shelter_lon = float(shelter_row['經度'])
        is_outdoor = not shelter_row['is_indoor']
        
        # 找到最近的AQI測站
        nearest_station, distance = self.calculate_nearest_aqi_station(shelter_lat, shelter_lon)
        
        if nearest_station is None:
            return {
                'risk_level': 'Unknown',
                'risk_color': 'gray',
                'nearest_aqi': None,
                'distance': None,
                'risk_reason': '無法找到最近的AQI測站'
            }
        
        nearest_aqi = nearest_station['aqi']
        
        # 風險評估邏輯
        if nearest_aqi > 100:
            risk_level = 'High Risk'
            risk_color = 'red'
            risk_reason = f'AQI > 100 (當前AQI: {nearest_aqi})'
        elif nearest_aqi > 50 and is_outdoor:
            risk_level = 'Warning'
            risk_color = 'orange'
            risk_reason = f'AQI > 50 且為室外避難所 (當前AQI: {nearest_aqi})'
        else:
            risk_level = 'Low Risk'
            risk_color = 'green'
            risk_reason = f'AQI ≤ 50 或為室內避難所 (當前AQI: {nearest_aqi})'
        
        return {
            'risk_level': risk_level,
            'risk_color': risk_color,
            'nearest_aqi': nearest_aqi,
            'distance': distance,
            'nearest_station': nearest_station['name'],
            'risk_reason': risk_reason
        }
    
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
        """創建空間疊圖地圖（風險分析版本）"""
        print("正在創建風險分析版Spatial Overlay地圖...")
        
        # 載入資料
        self.aqi_data = self.create_mock_aqi_data()
        new_shelter_data = self.load_new_shelter_data()
        
        if new_shelter_data.empty:
            print("無法載入避難所資料")
            return None, 0, 0
        
        # 使用邊界過濾
        self.shelter_data = self.filter_shelters_with_boundary(new_shelter_data)
        
        print(f"AQI測站數量: {len(self.aqi_data)}")
        print(f"避難所數量: {len(self.shelter_data)}")
        
        # 風險分析
        print("正在進行風險分析...")
        high_risk_count = 0
        warning_count = 0
        low_risk_count = 0
        
        for idx, shelter in self.shelter_data.iterrows():
            risk_assessment = self.assess_shelter_risk(shelter)
            self.shelter_data.loc[idx, 'risk_level'] = risk_assessment['risk_level']
            self.shelter_data.loc[idx, 'risk_color'] = risk_assessment['risk_color']
            self.shelter_data.loc[idx, 'nearest_aqi'] = risk_assessment['nearest_aqi']
            self.shelter_data.loc[idx, 'distance_to_aqi'] = risk_assessment['distance']
            self.shelter_data.loc[idx, 'nearest_station'] = risk_assessment['nearest_station']
            self.shelter_data.loc[idx, 'risk_reason'] = risk_assessment['risk_reason']
            
            if risk_assessment['risk_level'] == 'High Risk':
                high_risk_count += 1
            elif risk_assessment['risk_level'] == 'Warning':
                warning_count += 1
            else:
                low_risk_count += 1
        
        print(f"風險分析結果:")
        print(f"  高風險: {high_risk_count} 個")
        print(f"  警告: {warning_count} 個")
        print(f"  低風險: {low_risk_count} 個")
        
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
        
        # 添加避難所圖層（按風險分組）
        high_risk_group = folium.FeatureGroup(name='高風險避難所')
        warning_group = folium.FeatureGroup(name='警告避難所')
        low_risk_group = folium.FeatureGroup(name='低風險避難所')
        
        for _, shelter in self.shelter_data.iterrows():
            try:
                # 獲取坐標
                if hasattr(shelter, 'geometry'):
                    lat, lon = shelter.geometry.y, shelter.geometry.x
                else:
                    lat = float(shelter['緯度'])
                    lon = float(shelter['經度'])
                
                is_indoor = shelter['is_indoor']
                name = shelter['避難收容處所名稱']
                address = shelter.get('避難收容處所地址', '未知地址')
                capacity = shelter.get('預計收容人數', '未知')
                county = shelter.get('縣市及鄉鎮市區', '未知')
                risk_level = shelter['risk_level']
                risk_color = shelter['risk_color']
                nearest_aqi = shelter['nearest_aqi']
                distance = shelter['distance_to_aqi']
                nearest_station = shelter['nearest_station']
                risk_reason = shelter['risk_reason']
                
                popup_content = f"""
                <b>{name}</b><br>
                縣市: {county}<br>
                地址: {address}<br>
                類型: {'室內' if is_indoor else '室外'}<br>
                收容人數: {capacity}<br>
                <hr>
                <b>風險評估</b><br>
                風險等級: {risk_level}<br>
                最近AQI測站: {nearest_station}<br>
                最近AQI值: {nearest_aqi}<br>
                距離: {distance:.2f} 公里<br>
                風險原因: {risk_reason}<br>
                <small>坐標: ({lat:.6f}, {lon:.6f})</small>
                """
                
                # 根據風險等級選擇圖標和顏色
                if risk_level == 'High Risk':
                    icon = folium.Icon(color='red', icon='exclamation-triangle', prefix='fa')
                    target_group = high_risk_group
                elif risk_level == 'Warning':
                    icon = folium.Icon(color='orange', icon='warning', prefix='fa')
                    target_group = warning_group
                else:
                    icon = folium.Icon(color='green', icon='check', prefix='fa')
                    target_group = low_risk_group
                
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_content, max_width=400),
                    icon=icon,
                    tooltip=f"{name} ({risk_level})"
                ).add_to(target_group)
                
            except Exception as e:
                continue
        
        # 添加圖層（順序：避難所 -> 熱力圖 -> AQI測站）
        high_risk_group.add_to(m)
        warning_group.add_to(m)
        low_risk_group.add_to(m)
        
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
        
        aqi_group.add_to(m)
        
        # 添加圖例
        legend_html = '''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 250px; height: 420px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:12px; padding: 10px">
        <h4>Spatial Overlay 圖例 (風險分析)</h4>
        <b>AQI 測站</b><br>
        <i class="fa fa-circle" style="color:green"></i> 良好 (0-50)<br>
        <i class="fa fa-circle" style="color:yellow"></i> 普通 (51-100)<br>
        <i class="fa fa-circle" style="color:orange"></i> 對敏感族群不健康 (101-150)<br>
        <i class="fa fa-circle" style="color:red"></i> 對所有族群不健康 (151-200)<br>
        <i class="fa fa-circle" style="color:purple"></i> 非常不健康 (201-300)<br>
        <i class="fa fa-circle" style="color:maroon"></i> 危害 (301+)<br><br>
        <b>避難所風險等級</b><br>
        <i class="fa fa-exclamation-triangle" style="color:red"></i> 高風險 (AQI > 100)<br>
        <i class="fa fa-warning" style="color:orange"></i> 警告 (AQI > 50 & 室外)<br>
        <i class="fa fa-check" style="color:green"></i> 低風險 (其他條件)<br><br>
        <b>風險評估邏輯</b><br>
        • AQI > 100 = 高風險<br>
        • AQI > 50 & 室外 = 警告<br>
        • 其他 = 低風險<br><br>
        <b>Haversine距離</b><br>
        • 計算避難所到最近AQI測站距離<br>
        • 地球半徑: 6371公里<br>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # 添加圖層控制
        folium.LayerControl().add_to(m)
        
        # 添加全屏功能
        from folium.plugins import Fullscreen
        Fullscreen().add_to(m)
        
        # 儲存地圖
        output_file = 'outputs/spatial_overlay_risk_analysis.html'
        m.save(output_file)
        
        print(f"地圖已儲存至: {output_file}")
        print(f"風險分析統計: 高風險 {high_risk_count} 個, 警告 {warning_count} 個, 低風險 {low_risk_count} 個")
        
        return output_file, high_risk_count, warning_count, low_risk_count

def main():
    """主程式"""
    print("=== Spatial Overlay: AQI 測站 + 避難所疊圖 (風險分析版本) ===")
    print("功能:")
    print("• Haversine距離計算")
    print("• Scenario injection")
    print("• 風險條件判斷:")
    print("  - AQI > 100 = High Risk")
    print("  - AQI > 50 & outdoor = warning")
    
    # 確保輸出目錄存在
    os.makedirs('outputs', exist_ok=True)
    
    # 創建地圖
    map_creator = SpatialOverlayRiskAnalysis()
    output_file, high_risk, warning, low_risk = map_creator.create_map()
    
    if output_file is None:
        print("地圖創建失敗")
        return
    
    print(f"\n風險分析版Spatial Overlay地圖創建完成！")
    print(f"檔案位置: {output_file}")
    print(f"高風險避難所: {high_risk} 個")
    print(f"警告避難所: {warning} 個")
    print(f"低風險避難所: {low_risk} 個")
    print(f"請用瀏覽器開啟查看完整的地圖和互動功能")
    print(f"此版本包含Haversine距離計算和風險條件判斷")

if __name__ == "__main__":
    main()
