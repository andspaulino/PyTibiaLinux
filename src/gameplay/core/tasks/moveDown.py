from src.utils.keyboard import press
from ...typings import Context
from .common.base import BaseTask


class MoveDown(BaseTask):
    def __init__(self, context, direction: str):
        super().__init__()
        self.name = 'moveDown'
        self.isRootTask = True
        self.direction = direction
        self.floorLevel = context['radar']['coordinate'][2] + 1

    # TODO: add unit tests
    # TODO: improve this code
    # Código original mantido comentado:
    # def do(self, context: Context) -> bool:
    #     direction = None
    #     if self.direction == 'north':
    #         direction = 'up'
    #     if self.direction == 'south':
    #         direction = 'down'
    #     if self.direction == 'west':
    #         direction = 'left'
    #     if self.direction == 'east':
    #         direction = 'right'
    #     press(direction)
    #     return context
    def do(self, context: Context) -> bool:
        direction = None
        if self.direction == 'north':
            direction = 'up'
        if self.direction == 'south':
            direction = 'down'
        if self.direction == 'west':
            direction = 'left'
        if self.direction == 'east':
            direction = 'right'
        currentZ = context['radar']['coordinate'][2] if context.get('radar', {}).get('coordinate') is not None else 'None'
        print(f"[MoveDown] Executando press({direction}) para descer. Andar atual Z={currentZ}, andar esperado Z={self.floorLevel}")
        press(direction)
        return context

    # TODO: add unit tests
    # Código original mantido comentado:
    # def did(self, context: Context) -> bool:
    #     return context['radar']['coordinate'][2] == self.floorLevel
    def did(self, context: Context) -> bool:
        coord = context.get('radar', {}).get('coordinate')
        if coord is None:
            print("[MoveDown] did() -> Radar retornou coordenada None!")
            return False
        hasMoved = coord[2] == self.floorLevel
        print(f"[MoveDown] did() -> Coordenada atual Z={coord[2]}, Esperado Z={self.floorLevel}, Sucesso={hasMoved}")
        if hasMoved:
            context['radar']['lastCoordinateVisited'] = coord
        return hasMoved
