from indicators.IndicatorModule import IndicatorModule

class Dummy(IndicatorModule):

    def fetch_data(self, date):
        pass
    
    def normalize(self, date):
        return None