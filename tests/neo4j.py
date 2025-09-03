class GraphDatabase:
    @staticmethod
    def driver(uri, auth=None):
        class DummyDriver:
            def session(self):
                class DummySession:
                    def run(self, *args, **kwargs):
                        class DummyResult:
                            def data(self):
                                return []
                            def single(self):
                                return None
                        return DummyResult()
                    def close(self):
                        pass
                return DummySession()
            def close(self):
                pass
        return DummyDriver()