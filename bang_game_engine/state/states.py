from __future__ import annotations

import abc
import enum
from dataclasses import dataclass

from bang_game_engine.action import Action, DropCard, SkipTurn, UseCard
from bang_game_engine.card import Card, CardSuits, CardTypes, CardValues
from bang_game_engine.constraint import Constraint
from bang_game_engine.engine import Engine
from bang_game_engine.state.interfaces import IStateNode
