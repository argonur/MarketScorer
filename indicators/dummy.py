from indicators.IndicatorModule import IndicatorModule

class Dummy(IndicatorModule):

    def fetch_data(self):
        pass
    
    def normalize(self):
        return None