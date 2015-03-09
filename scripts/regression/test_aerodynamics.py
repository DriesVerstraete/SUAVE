# test_aerodynamics
#
# Created:  Tim MacDonald - 09/09/14
# Modified: Tim MacDonald - 09/10/14

import SUAVE
from SUAVE.Core import Units
from SUAVE.Core import Data
#from SUAVE.Methods.Aerodynamics.Lift import compute_aircraft_lift
#from SUAVE.Methods.Aerodynamics.Drag import compute_aircraft_drag

from SUAVE.Methods.Aerodynamics.Fidelity_Zero.Lift import compute_aircraft_lift
from SUAVE.Methods.Aerodynamics.Fidelity_Zero.Drag import compute_aircraft_drag

from test_mission_B737 import vehicle_setup

import numpy as np
import pylab as plt

import copy, time
from copy import deepcopy
import random

def main():
    
    vehicle = vehicle_setup() # Create the vehicle for testing
    for wing in vehicle.wings:
        wing.areas.wetted   = 2.0 * wing.areas.reference
        wing.areas.exposed  = 0.8 * wing.areas.wetted
        wing.areas.affected = 0.6 * wing.areas.wetted    
    aerodynamics = SUAVE.Analyses.Aerodynamics.Fidelity_Zero()
    aerodynamics.geometry = vehicle
    aerodynamics.settings.drag_coefficient_increment = 0.0000
    vehicle.aerodynamics_model = aerodynamics   
    vehicle.aerodynamics_model.finalize()
    
    test_num = 11 # Length of arrays used in this test
    
    # --------------------------------------------------------------------
    # Test Lift Surrogate
    # --------------------------------------------------------------------    
    
    AoA = np.linspace(-.174,.174,test_num) # +- 10 degrees
    
    lift_model = vehicle.aerodynamics_model.surrogates.lift_coefficient
    
    wing_lift = lift_model(AoA)
    
    wing_lift_r = np.array([-0.79420805, -0.56732369, -0.34043933, -0.11355497,  0.11332939,
                            0.34021374,  0.5670981 ,  0.79398246,  1.02086682,  1.24775117,
                            1.47463553])
    
    surg_test = np.abs((wing_lift-wing_lift_r)/wing_lift)
    
    print 'Surrogate Test Results \n'
    print surg_test
    
    assert(np.max(surg_test)<1e-4), 'Aero regression failed at surrogate test'

    
    # --------------------------------------------------------------------
    # Initialize variables needed for CL and CD calculations
    # Use a seeded random order for values
    # --------------------------------------------------------------------
    
    random.seed(1)
    Mc = np.linspace(0.05,0.9,test_num)
    random.shuffle(Mc)
    rho = np.linspace(0.3,1.3,test_num)
    random.shuffle(rho)
    mu = np.linspace(5*10**-6,20*10**-6,test_num)
    random.shuffle(mu)
    T = np.linspace(200,300,test_num)
    random.shuffle(T)
    pressure = np.linspace(10**5,10**6,test_num)

    
    conditions = Data()
    
    conditions.freestream = Data()
    conditions.freestream.mach_number = Mc
    conditions.freestream.density = rho
    conditions.freestream.viscosity = mu
    conditions.freestream.temperature = T
    conditions.freestream.pressure = pressure
    
    conditions.aerodynamics = Data()
    conditions.aerodynamics.angle_of_attack = AoA
    conditions.aerodynamics.lift_breakdown = Data()
    conditions.aerodynamics.lift_breakdown.inviscid_wings_lift = wing_lift
    
    configuration = vehicle.aerodynamics_model.settings
    
    conditions.aerodynamics.drag_breakdown = Data()

    geometry = Data()
    for k in ['fuselages','wings','propulsors']:
        geometry[k] = deepcopy(vehicle[k])    
    geometry.reference_area = vehicle.reference_area  
    #geometry.wings[0] = Data()
    #geometry.wings[0].vortex_lift = False
    
    # --------------------------------------------------------------------
    # Test compute Lift
    # --------------------------------------------------------------------
    
    compute_aircraft_lift(conditions, configuration, geometry) 
    
    lift = conditions.aerodynamics.lift_breakdown.total
    lift_r = np.array([-2.07712357, -0.73495391, -0.38858687, -0.1405849 ,  0.22295808,
                       0.5075275 ,  0.67883681,  0.92787301,  1.40470556,  2.08126751,
                       1.69661601])
    
    lift_test = np.abs((lift-lift_r)/lift)
    
    print '\nCompute Lift Test Results\n'
    print lift_test
        
    assert(np.max(lift_test)<1e-4), 'Aero regression failed at compute lift test'    
    
    
    # --------------------------------------------------------------------
    # Test compute drag 
    # --------------------------------------------------------------------
    
    compute_aircraft_drag(conditions, configuration, geometry)
    
    # Pull calculated values
    drag_breakdown = conditions.aerodynamics.drag_breakdown
    
    # Only one wing is evaluated since they rely on the same function
    cd_c           = drag_breakdown.compressible['main_wing'].compressibility_drag
    cd_i           = drag_breakdown.induced.total
    cd_m           = drag_breakdown.miscellaneous.total
    # cd_m_fuse_base = drag_breakdown.miscellaneous.fuselage_base
    # cd_m_fuse_up   = drag_breakdown.miscellaneous.fuselage_upsweep
    # cd_m_nac_base  = drag_breakdown.miscellaneous.nacelle_base['turbo_fan']
    # cd_m_ctrl      = drag_breakdown.miscellaneous.control_gaps
    cd_p_fuse      = drag_breakdown.parasite['fuselage'].parasite_drag_coefficient
    cd_p_wing      = drag_breakdown.parasite['main_wing'].parasite_drag_coefficient
    cd_tot         = drag_breakdown.total
    
    (cd_c_r, cd_i_r, cd_m_r, cd_m_fuse_base_r, cd_m_fuse_up_r, cd_m_nac_base_r, cd_m_ctrl_r, cd_p_fuse_r, cd_p_wing_r, cd_tot_r) = reg_values()
    
    drag_tests = Data()
    drag_tests.cd_c = np.abs((cd_c-cd_c_r)/cd_c)
    drag_tests.cd_i = np.abs((cd_i-cd_i_r)/cd_i)
    drag_tests.cd_m = np.abs((cd_m-cd_m_r)/cd_m)
    # Line below is not normalized since regression values are 0, insert commented line if this changes
    # drag_tests.cd_m_fuse_base = np.abs((cd_m_fuse_base-cd_m_fuse_base_r)) # np.abs((cd_m_fuse_base-cd_m_fuse_base_r)/cd_m_fuse_base)
    # drag_tests.cd_m_fuse_up   = np.abs((cd_m_fuse_up - cd_m_fuse_up_r)/cd_m_fuse_up)
    # drag_tests.cd_m_ctrl      = np.abs((cd_m_ctrl - cd_m_ctrl_r)/cd_m_ctrl)
    drag_tests.cd_p_fuse      = np.abs((cd_p_fuse - cd_p_fuse_r)/cd_p_fuse)
    drag_tests.cd_p_wing      = np.abs((cd_p_wing - cd_p_wing_r)/cd_p_wing)
    drag_tests.cd_tot         = np.abs((cd_tot - cd_tot_r)/cd_tot)
    
    print '\nCompute Drag Test Results\n'
    print drag_tests
    
    for i, tests in drag_tests.items():
        assert(np.max(tests)<1e-4),'Aero regression test failed at ' + i
    
    return conditions, configuration, geometry, test_num
      

def reg_values():
    cd_c_r = np.array([  1.41429794e-08,   2.96579619e-09,   1.03047740e-22,   4.50771390e-09,
                         1.27784183e-03,   1.31214322e-04,   3.98984222e-09,   6.19742191e-11,
                         8.21182714e-05,   1.20217216e-03,   5.63926215e-14])
    
    cd_i_r = np.array([ 0.17295472,  0.02165349,  0.00605319,  0.00079229,  0.00199276,
                        0.01032588,  0.01847305,  0.03451317,  0.07910034,  0.17364551,
                        0.11539178])
    cd_m_r = np.array([ 0.00047933,  0.00047933,  0.00047933,  0.00047933,  0.00047933,
                        0.00047933,  0.00047933,  0.00047933,  0.00047933,  0.00047933,
                        0.00047933])
    
    cd_m_fuse_base_r = np.array([ 0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.])
    
    cd_m_fuse_up_r   = np.array([  4.80530506e-05,   4.80530506e-05,   4.80530506e-05,
                                   4.80530506e-05,   4.80530506e-05,   4.80530506e-05,
                                   4.80530506e-05,   4.80530506e-05,   4.80530506e-05,
                                   4.80530506e-05,   4.80530506e-05])
    
    cd_m_nac_base_r = np.array([ 0.00033128,  0.00033128,  0.00033128,  0.00033128,  0.00033128,
                                0.00033128,  0.00033128,  0.00033128,  0.00033128,  0.00033128,
                                0.00033128])
    
    cd_m_ctrl_r     = np.array([ 0.0001,  0.0001,  0.0001,  0.0001,  0.0001,  0.0001,  0.0001,
                                 0.0001,  0.0001,  0.0001,  0.0001])
    
    cd_p_fuse_r     = np.array([  0.00861449,  0.01003034,  0.01543476,  0.00983168,  0.01004746,
                                  0.00840775,  0.01029339,  0.01273788,  0.01002575,  0.00900746,
                                  0.01043446])
    
    cd_p_wing_r     = np.array([ 0.00398269,  0.00401536,  0.00619387,  0.00388993,  0.00442375,
                                 0.00343623,  0.00405385,  0.00506457,  0.00406928,  0.00379353,
                                 0.00407611])
    
    cd_tot_r        = np.array([ 0.19427599,  0.03976739,  0.0332802 ,  0.01807724,  0.02206145,
                                 0.02565411,  0.0368808 ,  0.05753452,  0.09852189,  0.19461151,
                                 0.13593163])
    
    return cd_c_r, cd_i_r, cd_m_r, cd_m_fuse_base_r, cd_m_fuse_up_r, cd_m_nac_base_r, cd_m_ctrl_r, cd_p_fuse_r, cd_p_wing_r, cd_tot_r

if __name__ == '__main__':
    (conditions, configuration, geometry, test_num) = main()
    
    print 'Aero regression test passed!'
    
    # --------------------------------------------------------------------
    # Drag Polar
    # --------------------------------------------------------------------  
    
    # Cruise conditions (except Mach number)
    conditions.freestream.mach_number = np.array([0.2]*test_num)
    conditions.freestream.density = np.array([0.3804534]*test_num)
    conditions.freestream.viscosity = np.array([1.43408227e-05]*test_num)
    conditions.freestream.temperature = np.array([218.92391647]*test_num)
    conditions.freestream.pressure = np.array([23908.73408391]*test_num)
    
    compute_aircraft_lift(conditions, configuration, geometry) # geometry is third variable, not used
    CL = conditions.aerodynamics.lift_breakdown.total    
    
    compute_aircraft_drag(conditions, configuration, geometry)
    CD = conditions.aerodynamics.drag_breakdown.total
    
    plt.figure("Drag Polar")
    axes = plt.gca()     
    axes.plot(CD,CL,'bo-')
    axes.set_xlabel('$C_D$')
    axes.set_ylabel('$C_L$')
    
    
    plt.show(block=True) # here so as to not block the regression test