#Este arquivo define a classe base para os agendadores de briefing. O agendador é responsável por determinar quando o briefing deve ser gerado e distribuído para os usuários. Ele pode usar uma biblioteca de agendamento, como APScheduler, para configurar tarefas periódicas que executam o BriefingAgent em horários específicos (por exemplo, diariamente às 8h). A classe BaseScheduler é uma classe abstrata que define a interface que todos os agendadores devem implementar, garantindo que o sistema possa usar qualquer implementação de agendamento de forma

from abc import ABC, abstractmethod


class BaseScheduler(ABC):
    """Abstract base class for briefing schedulers."""

    @abstractmethod
    def start(self) -> None:
        """Start the scheduler."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop the scheduler."""
        ...