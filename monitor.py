#!/usr/bin/env python3
"""
Monitor em tempo real do processo de avaliação
"""

import time
import json
from pathlib import Path
from datetime import datetime

class MonitorAvaliacao:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        
    def monitorar_progresso(self, intervalo: int = 5):
        """Monitora progresso em tempo real"""
        print("🔍 Monitorando progresso da avaliação...")
        print("Pressione Ctrl+C para parar\n")
        
        try:
            while True:
                stats = self._calcular_estatisticas()
                self._exibir_progresso(stats)
                time.sleep(intervalo)
        except KeyboardInterrupt:
            print("\n✅ Monitoramento finalizado")
    
    def _calcular_estatisticas(self) -> dict:
        """Calcula estatísticas atuais"""
        feedbacks_dir = self.output_dir / "feedbacks"
        if not feedbacks_dir.exists():
            return {"total": 0, "processados": 0, "taxa": 0.0}
        
        arquivos_feedback = list(feedbacks_dir.glob("*_feedback.txt"))
        processados = len(arquivos_feedback)
        
        # Estima total baseado em logs (implementação simplificada)
        total = processados  # Poderia ser obtido de arquivo de configuração
        
        taxa = (processados / total * 100) if total > 0 else 0
        
        return {
            "total": total,
            "processados": processados,
            "taxa": taxa,
            "timestamp": datetime.now()
        }
    
    def _exibir_progresso(self, stats: dict):
        """Exibe progresso formatado"""
        print(f"\r🚀 Progresso: {stats['processados']}/{stats['total']} "
              f"({stats['taxa']:.1f}%) - {stats['timestamp'].strftime('%H:%M:%S')}", 
              end="", flush=True)

if __name__ == "__main__":
    monitor = MonitorAvaliacao()
