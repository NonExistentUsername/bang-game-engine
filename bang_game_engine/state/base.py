import abc
import logging

from bang_game_engine.action import Action
from bang_game_engine.engine import Engine
from bang_game_engine.state.interfaces import IStateNode

logger = logging.getLogger(__name__)


class BaseStateNode(IStateNode):
    def __init__(
        self,
        is_done: bool = False,
        child_node: IStateNode | None = None,
    ):
        super().__init__()
        self.__is_done = is_done
        self.__child_node = child_node

    @property
    def is_done(self) -> bool:
        return self.__is_done

    def next(self, user_action: Action | None = None) -> None:
        if self.__child_node is not None:
            logger.debug(
                f"Child node is set, applying user action: {user_action} (class: {self.__class__.__name__})"
            )
            try:
                self.__child_node.next(user_action)
                return
            except StopIteration:
                logger.debug(
                    f"Child node is done. Resetting child node (class: {self.__class__.__name__})"
                )
                # Reset child node
                self.__child_node = None
                # Return, because child node is already applied
                return
            except Exception as e:
                logger.error(
                    f"Error while applying user action: {user_action} (class: {self.__class__.__name__})"
                )
                raise e
        else:
            logger.debug(
                f"No child node is set, applying user action: {user_action} (class: {self.__class__.__name__})"
            )

        if self.__is_done:
            logger.debug(
                f"Node is done. Raising StopIteration (class: {self.__class__.__name__})"
            )
            raise StopIteration()

        self._next(user_action)

    def _mark_as_done(self) -> None:
        logger.debug(f"Marking node as done (class: {self.__class__.__name__})")
        self.__is_done = True

    def _set_child_node(self, child_node: IStateNode) -> None:
        logger.debug(
            f"Setting child node: {child_node} (class: {self.__class__.__name__})"
        )
        if self.__child_node is not None:
            raise ValueError("Child node is already set")

        self.__child_node = child_node

    @abc.abstractmethod
    def _next(self, user_action: Action | None = None) -> None:
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(is_done={self.__is_done}, child_node={self.__child_node})"
