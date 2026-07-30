import json
import os
import re
import stat
import tempfile
from copy import deepcopy
from pathlib import Path

from .schema import ROUTE_FILE_SUFFIX, RouteDocument
from .validator import validateRouteDocument


DEFAULT_ROUTES_DIRECTORY = Path(__file__).resolve().parents[2] / 'routes'
MAX_ROUTE_FILE_SIZE_BYTES = 5 * 1024 * 1024
ROUTE_FILE_STEM_PATTERN = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')


class RouteStore:
    def __init__(self, routesDirectory: Path):
        self.routesDirectory = routesDirectory

    def _validateRouteFileName(self, routeFile: str) -> Path:
        if not isinstance(routeFile, str) or routeFile == '':
            raise ValueError('routeFile deve ser um nome de arquivo')
        if '/' in routeFile or '\\' in routeFile or '..' in routeFile:
            raise ValueError('routeFile deve conter somente o nome do arquivo')
        routePath = Path(routeFile)
        if routePath.is_absolute() or routePath.name != routeFile:
            raise ValueError('routeFile deve ser relativo ao diretório de rotas')
        if routePath.suffix != ROUTE_FILE_SUFFIX:
            raise ValueError(f'routeFile deve terminar com {ROUTE_FILE_SUFFIX}')
        if ROUTE_FILE_STEM_PATTERN.fullmatch(routePath.stem) is None:
            raise ValueError(
                'routeFile deve usar um slug minúsculo separado por hífens'
            )
        return self.routesDirectory / routePath

    def _validateRoutesDirectory(self) -> None:
        currentPath = self.routesDirectory.absolute()
        while True:
            if currentPath.is_symlink():
                raise ValueError(
                    'o diretório de rotas não pode atravessar links simbólicos'
                )
            if currentPath.parent == currentPath:
                break
            currentPath = currentPath.parent
        if self.routesDirectory.exists() and not self.routesDirectory.is_dir():
            raise ValueError('o caminho de rotas deve ser um diretório')



    def listRoutes(self) -> list[str]:
        self._validateRoutesDirectory()
        if not self.routesDirectory.exists():
            return []
        return sorted(
            path.name
            for path in self.routesDirectory.iterdir()
            if (
                path.is_file()
                and not path.is_symlink()
                and path.suffix == ROUTE_FILE_SUFFIX
            )
        )

    def load(self, routeFile: str) -> RouteDocument:
        routePath = self._validateRouteFileName(routeFile)
        self._validateRoutesDirectory()
        if routePath.is_symlink():
            raise ValueError('o arquivo de rota não pode ser um link simbólico')
        descriptor: int | None = None
        try:
            descriptor = os.open(
                routePath,
                os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0),
            )
            fileStatus = os.fstat(descriptor)
            if not stat.S_ISREG(fileStatus.st_mode):
                raise ValueError('o arquivo de rota deve ser um arquivo regular')
            if fileStatus.st_size > MAX_ROUTE_FILE_SIZE_BYTES:
                raise ValueError(
                    'o arquivo de rota excede o limite de '
                    f'{MAX_ROUTE_FILE_SIZE_BYTES} bytes'
                )
            with os.fdopen(descriptor, 'r', encoding='utf-8') as routeFileHandle:
                descriptor = None
                rawDocument = json.load(routeFileHandle)
        finally:
            if descriptor is not None:
                os.close(descriptor)
        document = validateRouteDocument(rawDocument)
        return deepcopy(document)

    def save(self, routeFile: str, document: object) -> RouteDocument:
        routePath = self._validateRouteFileName(routeFile)
        validatedDocument = validateRouteDocument(document)
        self._validateRoutesDirectory()
        self.routesDirectory.mkdir(parents=True, exist_ok=True)
        self._validateRoutesDirectory()
        if routePath.is_symlink():
            raise ValueError('o arquivo de rota não pode ser um link simbólico')

        temporaryPath: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8',
                dir=self.routesDirectory,
                prefix=f'.{routePath.stem}-',
                suffix='.tmp',
                delete=False,
            ) as temporaryFile:
                temporaryPath = Path(temporaryFile.name)
                json.dump(
                    validatedDocument,
                    temporaryFile,
                    ensure_ascii=False,
                    indent=2,
                )
                temporaryFile.write('\n')
                temporaryFile.flush()
                os.fsync(temporaryFile.fileno())
            os.replace(temporaryPath, routePath)
            temporaryPath = None
            directoryDescriptor = os.open(
                self.routesDirectory,
                os.O_RDONLY
                | getattr(os, 'O_DIRECTORY', 0)
                | getattr(os, 'O_NOFOLLOW', 0),
            )
            try:
                os.fsync(directoryDescriptor)
            finally:
                os.close(directoryDescriptor)
        finally:
            if temporaryPath is not None:
                temporaryPath.unlink(missing_ok=True)

        return deepcopy(validatedDocument)
