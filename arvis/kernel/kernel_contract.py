# arvis/kernel/kernel_contract.py

class CognitiveKernelContract:

    def observe(self):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError

    def stabilize(self):
        raise NotImplementedError