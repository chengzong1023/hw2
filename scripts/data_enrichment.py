#!/usr/bin/env python3
"""
避難收容處所資料增強程式
使用AI根據設施名稱推斷是否為室內避難所
"""

import pandas as pd
import re
import numpy as np
from typing import Dict, List, Tuple

class ShelterDataEnrichment:
    def __init__(self, csv_file):
        self.df = pd.read_csv(csv_file, encoding='utf-8-sig')
        
        # 室外設施關鍵字
        self.outdoor_keywords = [
            '公園', '廣場', '體育場', '運動場', '球場', '田徑場', 
            '停車場', '河濱公園', '森林', '山', '步道', '營地',
            '海濱', '沙灘', '碼頭', '港', '堤防', '綠地',
            '開放空間', '戶外', '露天', 'sky', 'park', 'square',
            'stadium', 'field', 'ground', 'outdoor'
        ]
        
        # 室內設施關鍵字
        self.indoor_keywords = [
            '學校', '活動中心', '社區中心', '集會所', '禮堂', '教室',
            '體育館', '健身房', '圖書館', '辦公處', '村辦公處',
            '里辦公處', '鄉公所', '鎮公所', '區公所', '市公所',
            '消防局', '警察局', '衛生所', '醫院', '診所',
            '寺廟', '教堂', '祠堂', '會館', '大樓', '大廈',
            '中心', '館', '堂', '樓', '室', '廳', '舍',
            'school', 'center', 'hall', 'building', 'office',
            'indoor', 'gym', 'library', 'clinic'
        ]
        
        # 模糊關鍵字（需要更多上下文判斷）
        self.ambiguous_keywords = [
            '中心', '館', '堂', '場', '園', '區'
        ]
    
    def extract_facility_features(self, facility_name: str) -> Dict[str, bool]:
        """提取設施特徵"""
        if pd.isna(facility_name):
            return {'has_outdoor': False, 'has_indoor': False, 'has_ambiguous': False}
        
        facility_name = str(facility_name).lower()
        
        features = {
            'has_outdoor': any(keyword in facility_name for keyword in self.outdoor_keywords),
            'has_indoor': any(keyword in facility_name for keyword in self.indoor_keywords),
            'has_ambiguous': any(keyword in facility_name for keyword in self.ambiguous_keywords)
        }
        
        return features
    
    def rule_based_classification(self, facility_name: str, address: str = "") -> bool:
        """基於規則的分類方法"""
        features = self.extract_facility_features(facility_name)
        
        # 明確室外設施
        if features['has_outdoor'] and not features['has_indoor']:
            return False
        
        # 明確室內設施
        if features['has_indoor'] and not features['has_outdoor']:
            return True
        
        # 特殊規則判斷
        facility_name = str(facility_name).lower()
        address = str(address).lower()
        
        # 學校相關通常為室內
        if any(word in facility_name for word in ['國小', '國中', '高中', '大學', '學校']):
            return True
        
        # 活動中心通常為室內
        if '活動中心' in facility_name:
            return True
        
        # 公園相關通常為室外
        if '公園' in facility_name:
            return False
        
        # 廣場相關通常為室外
        if '廣場' in facility_name:
            return False
        
        # 體育相關需要進一步判斷
        if '體育' in facility_name:
            if '館' in facility_name or '室' in facility_name:
                return True  # 體育館、體育室
            else:
                return False  # 體育場、運動場
        
        # 辦公處相關通常為室內
        if any(word in facility_name for word in ['辦公處', '公所']):
            return True
        
        # 社區相關通常為室內
        if '社區' in facility_name and ('中心' in facility_name or '集會' in facility_name):
            return True
        
        # 宗教場所通常為室內
        if any(word in facility_name for word in ['寺', '廟', '教堂', '祠堂']):
            return True
        
        # 預設為室內（安全原則）
        return True
    
    def ai_enhanced_classification(self, facility_name: str, address: str = "", 
                                 original_indoor: str = "", original_outdoor: str = "") -> Tuple[bool, str]:
        """AI增強分類方法"""
        
        # 基於原始資料的判斷
        if pd.notna(original_indoor) and original_indoor == '是':
            return True, "基於原始室內標記"
        
        if pd.notna(original_outdoor) and original_outdoor == '是':
            return False, "基於原始室外標記"
        
        # 基於規則的判斷
        rule_result = self.rule_based_classification(facility_name, address)
        reasoning = "基於規則推斷"
        
        # 進一步的AI推理
        facility_name = str(facility_name).strip()
        
        # 分析設施名稱的複合特徵
        if '活動中心' in facility_name:
            reasoning += " (活動中心通常為室內設施)"
            return True, reasoning
        
        elif '公園' in facility_name:
            reasoning += " (公園通常為室外空間)"
            return False, reasoning
        
        elif '廣場' in facility_name:
            reasoning += " (廣場通常為室外空間)"
            return False, reasoning
        
        elif '學校' in facility_name:
            reasoning += " (學校建築通常為室內)"
            return True, reasoning
        
        elif any(word in facility_name for word in ['體育館', '健身館']):
            reasoning += " (體育館為室內設施)"
            return True, reasoning
        
        elif any(word in facility_name for word in ['體育場', '運動場']):
            reasoning += " (體育場為室外設施)"
            return False, reasoning
        
        else:
            reasoning += " (預設為室內 - 安全原則)"
            return True, reasoning
    
    def enrich_data(self):
        """增強資料"""
        print("開始進行資料增強...")
        
        results = []
        indoor_count = 0
        outdoor_count = 0
        
        for idx, row in self.df.iterrows():
            facility_name = row.get('避難收容處所名稱', '')
            address = row.get('避難收容處所地址', '')
            original_indoor = row.get('室內', '')
            original_outdoor = row.get('室外', '')
            
            # AI增強分類
            is_indoor, reasoning = self.ai_enhanced_classification(
                facility_name, address, original_indoor, original_outdoor
            )
            
            # 統計
            if is_indoor:
                indoor_count += 1
            else:
                outdoor_count += 1
            
            # 記錄結果
            result = {
                '序號': row.get('序號', ''),
                '避難收容處所名稱': facility_name,
                '地址': address,
                'is_indoor': is_indoor,
                'classification_reasoning': reasoning,
                'original_indoor': original_indoor,
                'original_outdoor': original_outdoor
            }
            
            results.append(result)
            
            # 顯示部分範例
            if idx < 10:
                print(f"{idx+1:3d}. {facility_name[:20]:20s} -> {'室內' if is_indoor else '室外':4s} ({reasoning})")
        
        # 創建新的DataFrame
        enriched_df = pd.DataFrame(results)
        
        # 統計報告
        total_count = len(enriched_df)
        print(f"\n=== 資料增強統計 ===")
        print(f"總處所數量: {total_count}")
        print(f"室內設施: {indoor_count} ({indoor_count/total_count*100:.1f}%)")
        print(f"室外設施: {outdoor_count} ({outdoor_count/total_count*100:.1f}%)")
        
        return enriched_df
    
    def analyze_classification_patterns(self, enriched_df):
        """分析分類模式"""
        print("\n=== 分類模式分析 ===")
        
        # 按設施類型分析
        facility_types = {}
        
        for _, row in enriched_df.iterrows():
            facility_name = row['避難收容處所名稱']
            is_indoor = row['is_indoor']
            
            # 提取設施類型關鍵字
            facility_type = "其他"
            
            if '活動中心' in facility_name:
                facility_type = "活動中心"
            elif '公園' in facility_name:
                facility_type = "公園"
            elif '學校' in facility_name:
                facility_type = "學校"
            elif '體育' in facility_name:
                facility_type = "體育設施"
            elif '辦公處' in facility_name or '公所' in facility_name:
                facility_type = "辦公處所"
            elif '社區' in facility_name:
                facility_type = "社區設施"
            elif '寺' in facility_name or '廟' in facility_name or '教堂' in facility_name:
                facility_type = "宗教場所"
            
            if facility_type not in facility_types:
                facility_types[facility_type] = {'室內': 0, '室外': 0}
            
            if is_indoor:
                facility_types[facility_type]['室內'] += 1
            else:
                facility_types[facility_type]['室外'] += 1
        
        print("設施類型分佈:")
        for facility_type, counts in sorted(facility_types.items(), key=lambda x: x[1]['室內'] + x[1]['室外'], reverse=True):
            total = counts['室內'] + counts['室外']
            indoor_pct = counts['室內'] / total * 100 if total > 0 else 0
            print(f"  {facility_type:8s}: 室內 {counts['室內']:3d} ({indoor_pct:5.1f}%) | 室外 {counts['室外']:3d} ({100-indoor_pct:5.1f}%)")
    
    def save_enriched_data(self, enriched_df):
        """儲存增強後的資料"""
        # 合併原始資料和增強資料
        merged_df = self.df.merge(
            enriched_df[['序號', 'is_indoor', 'classification_reasoning']], 
            on='序號', 
            how='left'
        )
        
        # 儲存完整增強資料
        merged_df.to_csv('data/shelter_locations_enriched.csv', index=False, encoding='utf-8-sig')
        print(f"\n增強資料已儲存至: data/shelter_locations_enriched.csv")
        
        # 儲存分類結果摘要
        summary_df = enriched_df[['避難收容處所名稱', 'is_indoor', 'classification_reasoning']]
        summary_df.to_csv('data/shelter_classification_summary.csv', index=False, encoding='utf-8-sig')
        print(f"分類摘要已儲存至: data/shelter_classification_summary.csv")
        
        return merged_df

def main():
    """主程式"""
    print("開始進行避難收容處所資料增強...")
    
    # 初始化增強器
    enricher = ShelterDataEnrichment('data/shelter_locations_cleaned.csv')
    
    # 進行資料增強
    enriched_df = enricher.enrich_data()
    
    # 分析分類模式
    enricher.analyze_classification_patterns(enriched_df)
    
    # 儲存增強資料
    final_df = enricher.save_enriched_data(enriched_df)
    
    print(f"\n資料增強完成！")
    print(f"新增欄位: is_indoor (布林值)")
    print(f"新增欄位: classification_reasoning (文字說明)")

if __name__ == "__main__":
    main()
