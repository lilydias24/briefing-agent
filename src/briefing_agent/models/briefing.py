# Aqui a gente vai definir os modelos de dados que a gente vai usar para representar as informações que a gente vai coletar e processar. Esses modelos vão ser usados para organizar os dados de forma estruturada, o que facilita o processamento e a geração do briefing final. A gente pode ter modelos para representar os artigos de notícias, os tópicos de interesse, as preferências do usuário, etc. O importante é que esses modelos sejam simples e fáceis de usar, para que a gente possa trabalhar com eles de forma eficiente.

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Article:
    """Represents a single news article."""

    title: str
    summary: str
    url: str
    source: str


@dataclass
class TopicBriefing:
    """Represents the briefing for a single topic."""

    topic: str
    articles: list[Article] = field(default_factory=list)


@dataclass
class Briefing:
    """Represents the full consolidated briefing to be sent."""

    topics: list[TopicBriefing] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)