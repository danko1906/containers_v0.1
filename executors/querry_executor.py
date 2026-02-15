from executors.dm_executor import DMExecutor
from executors.user_executor import UserExecutor
from executors.container_executor import ContainerExecutor


class QueryExecutor:
    def __init__(self, dm_executor: DMExecutor, container_executor: ContainerExecutor, user_executor: UserExecutor):
        self.dm = dm_executor
        self.containers = container_executor
        self.user = user_executor
