#Este arquivo define a classe base para os agentes. Cada agente é responsável por executar uma tarefa específica, como coletar informações, processar dados, gerar o briefing final, etc. A classe BaseAgent é uma classe abstrata que define a interface que todos os agentes devem implementar. Isso garante que o sistema possa usar qualquer agente de forma consistente, sem se preocupar com os detalhes de implementação de cada um.

from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    @abstractmethod
    def run(self, *args, **kwargs):
        """Execute the agent's main action."""
        ...