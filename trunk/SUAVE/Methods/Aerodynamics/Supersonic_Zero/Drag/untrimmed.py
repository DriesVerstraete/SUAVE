# untrimmed.py
# 
# Created:  Aug 2014, T. MacDonald
# Modified: Nov 2016, T. MacDonald

# ----------------------------------------------------------------------
#  Imports
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
#  Computes the miscellaneous drag
# ----------------------------------------------------------------------
def untrimmed(state,settings,geometry):

    # unpack inputs

    conditions    = state.conditions
    configuration = settings
    
    drag_breakdown             = conditions.aerodynamics.drag_breakdown

    # various drag components
    parasite_total        = conditions.aerodynamics.drag_breakdown.parasite.total            
    induced_total         = conditions.aerodynamics.drag_breakdown.induced.total            
    compressibility_total = conditions.aerodynamics.drag_breakdown.compressible.total         
    miscellaneous_drag    = conditions.aerodynamics.drag_breakdown.miscellaneous.total 

    # untrimmed drag
    aircraft_untrimmed = parasite_total        \
                       + induced_total         \
                       + compressibility_total \
                       + miscellaneous_drag
    
    conditions.aerodynamics.drag_breakdown.untrimmed = aircraft_untrimmed
    
    return aircraft_untrimmed
