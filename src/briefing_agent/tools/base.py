#Esse arquivo define a classe base para as ferramentas do agente. Cada ferramenta é uma ação específica que o agente pode executar, como buscar notícias, processar dados, gerar resumos, etc. A classe BaseTool é uma classe abstrata que define a interface que todas as ferramentas devem implementar. Isso garante que o agente possa usar qualquer ferramenta de forma consistente, sem se preocupar com os detalhes de implementação de cada uma.

from abc import ABC, abstractmethod


class BaseTool(ABC):
    """Abstract base class for all agent tools."""

    @abstractmethod
    def run(self, *args, **kwargs):
        """Execute the tool's main action."""
        ...