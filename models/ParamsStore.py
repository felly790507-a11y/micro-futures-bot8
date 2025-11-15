# strategy_v4/models/ParamsStore.py

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class ParamsStore:
    """
    權重參數儲存器：
    - 集中管理回歸權重
    - 支援版本控制
    - JSON 儲存與載入
    """

    def __init__(self, file_path: str = "calibrated_params.json"):
        self.path = Path(file_path)
        self._weights: Dict[str, float] = {}
        self._version: str = "unversioned"

    def load(self) -> None:
        """載入 JSON 權重檔"""
        if self.path.exists():
            try:
                with self.path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._weights = data.get("weights", {})
                    self._version = data.get("version", "unversioned")
            except (json.JSONDecodeError, OSError) as e:
                print(f"[ParamsStore] 載入失敗，使用預設值：{e}")
                self._weights = {}
                self._version = "unversioned"
        else:
            self._weights = {}
            self._version = "unversioned"

    def save(self) -> None:
        """儲存 JSON 權重檔"""
        data = {
            "weights": self._weights,
            "version": self._version
        }
        try:
            with self.path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"[ParamsStore] 儲存失敗：{e}")

    def update(self, version: str, weights: Dict[str, float], auto_timestamp: bool = True) -> None:
        """
        更新權重並儲存
        :param version: 權重版本號
        :param weights: 權重字典
        :param auto_timestamp: 是否自動附加時間戳記
        """
        if auto_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            version = f"{version}-{timestamp}"
        self._version = version
        self._weights = weights
        self.save()
        print(f"[ParamsStore] 已更新版本 {self._version}")

    def get_weights(self) -> Dict[str, float]:
        """取得權重字典"""
        return self._weights

    def get_version(self) -> str:
        """取得版本號"""
        return self._version

    def has_weights(self) -> bool:
        """檢查是否已有權重"""
        return bool(self._weights)

    def reset(self) -> None:
        """重置權重與版本"""
        self._weights = {}
        self._version = "unversioned"
        self.save()
        print("[ParamsStore] 已重置為預設狀態")
