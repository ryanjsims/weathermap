from holidays.countries.united_states import UnitedStates
from datetime import date
from lunarcalendar.festival import festivals

from dateutil.relativedelta import relativedelta as rd, MO, TH, SU
from dateutil.easter import easter

from holidays.constants import FRI, SAT, SUN
from holidays.constants import JAN, FEB, MAR, MAY, JUN, JUL, SEP, OCT, NOV, DEC

class WeatherportalHolidays(UnitedStates):
    def _populate(self, year):
        # New Year's Day
        if year > 1870:
            name = "New Year's Day"
            self[date(year, JAN, 1)] = name
            if self.observed and date(year, JAN, 1).weekday() == SUN:
                self[date(year, JAN, 1) + rd(days=+1)] = name + " (Observed)"
            elif self.observed and date(year, JAN, 1).weekday() == SAT:
                # Add Dec 31st from the previous year without triggering
                # the entire year to be added
                expand = self.expand
                self.expand = False
                self[date(year, JAN, 1) + rd(days=-1)] = name + " (Observed)"
                self.expand = expand
            # The next year's observed New Year's Day can be in this year
            # when it falls on a Friday (Jan 1st is a Saturday)
            if self.observed and date(year, DEC, 31).weekday() == FRI:
                self[date(year, DEC, 31)] = name + " (Observed)"

        # Martin Luther King Jr. Day
        if year >= 1986:
            name = "Dr. Martin Luther King Jr./Civil Rights Day"
            self[date(year, JAN, 1) + rd(weekday=MO(+3))] = name
        
        # Valentine's Day
        name = "Valentine's Day"
        self[date(year, FEB, 14)] = name

        # St. Patrick's Day
        name = "St. Patrick's Day"
        self[date(year, MAR, 17)] = name

        # Easter Sunday
        self[easter(year)] = "Easter Sunday"

        # Mother's Day
        name = "Mother's Day"
        self[date(year, MAY, 1) + rd(weekday=SU(+2))] = name

        # Juneteenth Day
        if year > 2020:
            self[date(year, JUN, 19)] = "Juneteenth National Independence Day"
        
        # Independence Day
        if year > 1870:
            name = "Independence Day"
            self[date(year, JUL, 4)] = name
            if self.observed and date(year, JUL, 4).weekday() == SAT:
                self[date(year, JUL, 4) + rd(days=-1)] = name + " (Observed)"
            elif self.observed and date(year, JUL, 4).weekday() == SUN:
                self[date(year, JUL, 4) + rd(days=+1)] = name + " (Observed)"

        # Mexican Independance Day
        name = "Día de la Independencia"
        self[date(year, SEP, 16)] = name
        if self.observed and date(year, SEP, 16).weekday() == SAT:
            self[date(year, SEP, 16) + rd(days=-1)] = name + " (Observed)"
        elif self.observed and date(year, SEP, 16).weekday() == SUN:
            self[date(year, SEP, 16) + rd(days=+1)] = name + " (Observed)"

        # Halloween
        self[date(year, OCT, 31)] = "Halloween"

        # Dia de los Muertos
        name = "Día de los Muertos"
        self[date(year, NOV, 2)] = name

        # Veterans Day
        if year > 1953:
            name = "Veterans Day"
        else:
            name = "Armistice Day"
        if 1978 > year > 1970:
            self[date(year, OCT, 1) + rd(weekday=MO(+4))] = name
        elif year >= 1938:
            self[date(year, NOV, 11)] = name
            if self.observed and date(year, NOV, 11).weekday() == SAT:
                self[date(year, NOV, 11) + rd(days=-1)] = name + " (Observed)"
            elif self.observed and date(year, NOV, 11).weekday() == SUN:
                self[date(year, NOV, 11) + rd(days=+1)] = name + " (Observed)"

        # Thanksgiving
        if year > 1870:
            self[date(year, NOV, 1) + rd(weekday=TH(+4))] = "Thanksgiving"

        # Christmas
        name = "Christmas Eve"
        self[date(year, DEC, 24)] = name

        name = "Christmas Day"
        self[date(year, DEC, 25)] = name

        # New Year's Eve
        name = "New Year's Eve"
        self[date(year, DEC, 31)] = name

        name = "Chinese New Year"
        for fest in festivals:
            if fest.get_lang("en") == name:
                cny = fest
                break
        self[cny(year)] = name
        #return super()._populate(year)

def escape_quote(s: str):
    if "'" in s:
        return "''".join(s.split("'"))
    return s

if __name__ == "__main__":
    h = WeatherportalHolidays(state="AZ")
    h._populate(2022)
    h.observed = False
    for key, value in sorted(list(h.items())):
        print("insert into holidays (name, message, path, palette_id) values ('" + escape_quote(value) + "'")
