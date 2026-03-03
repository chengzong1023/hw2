#!/usr/bin/env python3
"""
調試AQI資料結構
"""

import requests
import json

def debug_aqi_data():
    """調試AQI資料結構"""
    api_key = "CWA-0F19593F-BC83-4B93-8224-B626FD1A8B5C"
    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001"
    
    try:
        response = requests.get(url, params={'Authorization': api_key})
        if response.status_code == 200:
            data = response.json()
            
            print("AQI資料結構分析:")
            print(f"總記錄數: {len(data['records'])}")
            
            # 檢查第一筆記錄的結構
            first_record = data['records'][0]
            print(f"\n第一筆記錄的欄位:")
            for key in first_record.keys():
                print(f"  {key}: {type(first_record[key])}")
            
            # 檢查GeoInfo結構
            if 'GeoInfo' in first_record:
                print(f"\nGeoInfo結構:")
                geo_info = first_record['GeoInfo']
                for key in geo_info.keys():
                    print(f"  {key}: {type(geo_info[key])}")
                
                if 'Coordinates' in geo_info:
                    print(f"\nCoordinates結構:")
                    coords = geo_info['Coordinates']
                    print(f"  類型: {type(coords)}")
                    if isinstance(coords, list) and len(coords) > 0:
                        print(f"  長度: {len(coords)}")
                        print(f"  第一個坐標: {coords[0]}")
                        for key in coords[0].keys():
                            print(f"    {key}: {coords[0][key]}")
            
            # 檢查AQI欄位
            print(f"\nAQI相關欄位:")
            for key in first_record.keys():
                if 'aqi' in key.lower() or 'AQI' in key:
                    print(f"  {key}: {first_record[key]}")
            
            # 顯示前3筆完整記錄
            print(f"\n前3筆記錄:")
            for i, record in enumerate(data['records'][:3]):
                print(f"\n記錄 {i+1}:")
                print(f"  SiteName: {record.get('SiteName', 'N/A')}")
                print(f"  County: {record.get('County', 'N/A')}")
                print(f"  AQI: {record.get('AQI', 'N/A')}")
                if 'GeoInfo' in record and 'Coordinates' in record['GeoInfo']:
                    coords = record['GeoInfo']['Coordinates']
                    if len(coords) > 0:
                        print(f"  坐標: {coords[0]}")
            
        else:
            print(f"API請求失敗: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"發生錯誤: {e}")

if __name__ == "__main__":
    debug_aqi_data()
