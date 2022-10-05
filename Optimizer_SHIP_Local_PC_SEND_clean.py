# -*- coding: utf-8 -*-
"""
Created on Thu Feb 18 10:49:28 2021

@author: jboyce
"""
import pulp
import os
import pandas as pd
import numpy as np
import time

# CONSIDER ADDING SUMMARY FOR UPB, COUNT, PT RATE, FS INFO

def main():
    t = time.time()    
    print('Optimizing')
    optimize_ebo()
    print('Getting Results')
    get_optimizer_results()
    elapsed_time = round((time.time() - t),1)
    print(time_string_util(elapsed_time))


def optimize_ebo():
    import pulp
    import pandas as pd
    import numpy as np
    
    
    # import the file to be optimized
    # cwd = os.getcwd()
    cwd = r'C:\Users\jboyce\Desktop\Optimizer Local'
    # optimizer_input_path = r'M:\Capital Markets\PIPE\EBO\Optimizer' # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    optimizer_input_path = cwd
    #optimizer_path = r'M:\Capital Markets\GNMA EBO Project\Python\Optimizer'
    #M:\Capital Markets\PIPE\EBO\Optimizer
    optimizer_filename = 'optimizer_input.xlsx' 
    optimizer_pathandfile = optimizer_input_path + '\\' + optimizer_filename
    df = pd.read_excel(optimizer_pathandfile).fillna(0, downcast='infer').set_index('LoanId')
    
    # ADD CLEANING OF NULLS/NANS FOR FIELDS
    
    print(df.head())
    
    # ADD FUNCTION FOR INV FLAG X UPB FOR TOTAL_INV <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # Note: FLAG_INV defines eligibility for allocation to the Investor as 1 in this column
    df['TOTAL_B1'] = df['FLAG_B1'] * df['(price_b1 X UPB) + Accrued Interest']
    df['TOTAL_B2'] = df['FLAG_B2'] * df['(price_b1 X UPB) + Accrued Interest']
    df['TOTAL_B1_UPB'] = df['CurrentPrincipalBalanceAmt'] 
    df['TOTAL_B7'] = df['FLAG_B7'] * df['CurrentPrincipalBalanceAmt'] 
    df['TOTAL_B3'] = df['FLAG_B3'] * df['CurrentPrincipalBalanceAmt'] 
    df['TOTAL_B4'] = df['FLAG_B4'] * df['CurrentPrincipalBalanceAmt'] 
    df['TOTAL_B6'] = df['FLAG_B6'] * df['CurrentPrincipalBalanceAmt']
    df['TOTAL_B8'] = df['FLAG_B8'] * df['CurrentPrincipalBalanceAmt']
    df['TOTAL_B5'] = df['FLAG_B5'] * df['CurrentPrincipalBalanceAmt']


    # Create starting loan list
    loan_list = list(df.index.values)
    #print(loan_list[0:5]) # prints first 5 loannums
    
    
    #SET DICTIONARIES
    # AFTER OPTIMIZER SETTING FUNCTION IS CREATED, MAKE A FUNCTION FOR SETTING NEC/TOTAL FOR ALL INVESTORS
    # Set total funding target for MM (including dlq interest)
    print('Setting Dictionaries')
    TOTAL_B1 = dict(zip(loan_list,df['TOTAL_B1']))
    TOTAL_B1_UPB = dict(zip(loan_list,df['TOTAL_B1_UPB']))
    TOTAL_B2 = dict(zip(loan_list,df['TOTAL_B2']))
    TOTAL_B3 = dict(zip(loan_list,df['TOTAL_B3'])) 
    TOTAL_B7 = dict(zip(loan_list,df['TOTAL_B7'])) 
    TOTAL_B4 = dict(zip(loan_list,df['TOTAL_B4'])) 
    TOTAL_B6 = dict(zip(loan_list,df['TOTAL_B6'])) 
    TOTAL_B8 = dict(zip(loan_list,df['TOTAL_B8'])) 
    TOTAL_B5 = dict(zip(loan_list,df['TOTAL_B5'])) 

    # Create dictionary for NEC of investors 
    NEC_B1 = dict(zip(loan_list,df['NEC_B1']))
    NEC_B2 = dict(zip(loan_list,df['NEC_B2']))
    NEC_B3 = dict(zip(loan_list,df['NEC_B3'])) 
    NEC_B7 = dict(zip(loan_list,df['NEC_B7'])) 
    NEC_B4 = dict(zip(loan_list,df['NEC_B4'])) 
    NEC_B6 = dict(zip(loan_list,df['NEC_B6'])) 
    NEC_B8 = dict(zip(loan_list,df['NEC_B8'])) 
    NEC_B5 = dict(zip(loan_list,df['NEC_B5'])) 

    # Create dictionary for WA price calcs in constraints
    WA_PRICE_UPB_B1 = dict(zip(loan_list,df['price_B1 X UPB']))
    WA_PRICE_UPB_B2 = dict(zip(loan_list,df['price_B1 X UPB']))
    WA_PRICE_UPB_B3 = dict(zip(loan_list,df['price_B3 X UPB']))
    WA_PRICE_UPB_B7 = dict(zip(loan_list,df['price_b7 X UPB']))
    WA_PRICE_UPB_B4 = dict(zip(loan_list,df['price_b4 X UPB']))
    WA_PRICE_UPB_B6 = dict(zip(loan_list,df['price_b6 X UPB'])) # might have to change this
    WA_PRICE_UPB_B6 = dict(zip(loan_list,df['price_b6 X UPB']))
    WA_PRICE_UPB_B5 = dict(zip(loan_list,df['price_b5 X UPB']))

    
    # Create dictionary for Apollo Pool 1 WA price calcs in constraints
    WA_PRICE_UPB_B6_Pool1 = dict(zip(loan_list,df['price_b6 x B6_pool1_upb']))
    TOTAL_B6_POOL1 = dict(zip(loan_list,df['B6_pool1_upb'])) 
    TOTAL_B6_POOL2 = dict(zip(loan_list,df['B6_pool2_upb'])) 

    
    # Create dictionary for Total VA/USDA
    TOTAL_VA_USDA = dict(zip(loan_list,df['TOTAL_VA_USDA']))
    
    # Create Special Ad Hoc Pool Flag
    TOTAL_POOL_CD_UPB = dict(zip(loan_list,df['POOL_CD_UPB'])) 
    TOTAL_POOL_AB_UPB = dict(zip(loan_list,df['POOL_AB_UPB'])) 
    
    # Create dictionary for WA DQ
    WA_DQ = dict(zip(loan_list,df['DelinquentPaymentCount x UPB'])) 

    # IMPORT INVESTOR TARGETS
    df_investor_targets = define_investor_targets()


    # SET DECISION VARIABLES
    # SET VARIABLES
    print('Setting Variables')

    # Set binary indicators for allocation to Invvestors
    b1_integer = pulp.LpVariable.dicts("B1_Selector",loan_list,0,1,pulp.LpBinary) 
    b2_integer = pulp.LpVariable.dicts("B2_Selector",loan_list,0,1,pulp.LpBinary) 
    b3_integer = pulp.LpVariable.dicts("B3_Selector",loan_list,0,1,pulp.LpBinary) 
    b7_integer = pulp.LpVariable.dicts("B7_Selector",loan_list,0,1,pulp.LpBinary) 
    b4_integer = pulp.LpVariable.dicts("B4_Selector",loan_list,0,1,pulp.LpBinary) 
    b6_integer = pulp.LpVariable.dicts("B6_Selector",loan_list,0,1,pulp.LpBinary) 
    b8_integer = pulp.LpVariable.dicts("B8_Selector",loan_list,0,1,pulp.LpBinary) 
    b5_integer = pulp.LpVariable.dicts("B5_Selector",loan_list,0,1,pulp.LpBinary) 
    

    # SET THE PULP PROBLEM
    print('Setting Up Problem')
    prob = pulp.LpProblem('Maximum_Profit',pulp.LpMaximize)
    
    total_NEC = pulp.lpSum([NEC_B1[i] * b1_integer[i] + NEC_B2[i] * b2_integer[i] + NEC_B3[i] * b3_integer[i] + NEC_B7[i] * b7_integer[i] + NEC_B4[i] * b4_integer[i] + NEC_B6[i] * b6_integer[i] + NEC_B8[i] * b8_integer[i] + NEC_B5[i] * b5_integer[i] for i in loan_list])

    print('Setting Objective')

    # OBJECTIVE to maximize
    prob += total_NEC
    #print(prob)
    
    print('Setting Constraints')
    # CONSTRAINTS
    # Constraints for Investor trade size
    prob += pulp.lpSum(TOTAL_B1[i] * b1_integer[i] for i in TOTAL_B1) <= df_investor_targets.loc['B1'].trade_size*1.0e6 
    prob += pulp.lpSum(TOTAL_B2[i] * b2_integer[i] for i in TOTAL_B2) <= df_investor_targets.loc['B2'].trade_size*1.0e6 
    prob += pulp.lpSum(TOTAL_B3[i] * b3_integer[i] for i in TOTAL_B3) <= df_investor_targets.loc['B3'].trade_size*1.0e6 
    prob += pulp.lpSum(TOTAL_B7[i] * b7_integer[i] for i in TOTAL_B7) <= df_investor_targets.loc['B7'].trade_size*1.0e6 
    prob += pulp.lpSum(TOTAL_B4[i] * b4_integer[i] for i in TOTAL_B4) <= df_investor_targets.loc['B4'].trade_size*1.0e6 
    prob += pulp.lpSum(TOTAL_B6[i] * b6_integer[i] for i in TOTAL_B6) <= df_investor_targets.loc['B6'].trade_size*1.0e6 
    prob += pulp.lpSum(TOTAL_B8[i] * b8_integer[i] for i in TOTAL_B8) <= df_investor_targets.loc['B8'].trade_size*1.0e6 
    prob += pulp.lpSum(TOTAL_B5[i] * b5_integer[i] for i in TOTAL_B5) <= df_investor_targets.loc['B5'].trade_size*1.0e6 

    # Constraints for WA PRICE UPB
    prob += pulp.lpSum(WA_PRICE_UPB_B1[i] * b1_integer[i] for i in TOTAL_B1_UPB) >= df_investor_targets.loc['B1'].price_min * pulp.lpSum(TOTAL_B1_UPB[i] * b1_integer[i] for i in TOTAL_B1_UPB)
    prob += pulp.lpSum(WA_PRICE_UPB_B2[i] * b2_integer[i] for i in TOTAL_B1_UPB) >= df_investor_targets.loc['B2'].price_min * pulp.lpSum(TOTAL_B1_UPB[i] * b2_integer[i] for i in TOTAL_B1_UPB)
    prob += pulp.lpSum(WA_PRICE_UPB_B3[i] * b3_integer[i] for i in TOTAL_B3) >= df_investor_targets.loc['B3'].price_min * pulp.lpSum(TOTAL_B3[i] * b3_integer[i] for i in TOTAL_B3)
    prob += pulp.lpSum(WA_PRICE_UPB_B7[i] * b7_integer[i] for i in TOTAL_B7) >= df_investor_targets.loc['B7'].price_min * pulp.lpSum(TOTAL_B7[i] * b7_integer[i] for i in TOTAL_B7)
    prob += pulp.lpSum(WA_PRICE_UPB_B4[i] * b4_integer[i] for i in TOTAL_B4) >= df_investor_targets.loc['B4'].price_min * pulp.lpSum(TOTAL_B4[i] * b4_integer[i] for i in TOTAL_B4)
    prob += pulp.lpSum(WA_PRICE_UPB_B6[i] * b6_integer[i] for i in TOTAL_B6) <= df_investor_targets.loc['B6'].price_cap * pulp.lpSum(TOTAL_B6[i] * b6_integer[i] for i in TOTAL_B6) 
    prob += pulp.lpSum(WA_PRICE_UPB_B5[i] * b5_integer[i] for i in TOTAL_B5) >= df_investor_targets.loc['B5'].price_min * pulp.lpSum(TOTAL_B5[i] * b5_integer[i] for i in TOTAL_B5)
    

    # Constraints for VA/USDA Total
    prob += pulp.lpSum(TOTAL_VA_USDA[i] * b7_integer[i] for i in TOTAL_B7) <= (1-df_investor_targets.loc['B7'].fha_pct_min) * pulp.lpSum(TOTAL_B7[i] * b7_integer[i] for i in TOTAL_B7)
    prob += pulp.lpSum(TOTAL_VA_USDA[i] * b6_integer[i] for i in TOTAL_B6) <= (1-df_investor_targets.loc['B6'].fha_pct_min) * pulp.lpSum(TOTAL_B6[i] * b6_integer[i] for i in TOTAL_B6)
    prob += pulp.lpSum(TOTAL_VA_USDA[i] * b8_integer[i] for i in TOTAL_B8) <= (1-df_investor_targets.loc['B8'].fha_pct_min) * pulp.lpSum(TOTAL_B8[i] * b8_integer[i] for i in TOTAL_B8)
    prob += pulp.lpSum(TOTAL_VA_USDA[i] * b4_integer[i] for i in TOTAL_B4) <= (1-df_investor_targets.loc['B4'].fha_pct_min) * pulp.lpSum(TOTAL_B4[i] * b4_integer[i] for i in TOTAL_B4)
    prob += pulp.lpSum(TOTAL_VA_USDA[i] * b3_integer[i] for i in TOTAL_B3) <= (1-df_investor_targets.loc['B3'].fha_pct_min) * pulp.lpSum(TOTAL_B3[i] * b3_integer[i] for i in TOTAL_B3)
    prob += pulp.lpSum(TOTAL_VA_USDA[i] * b5_integer[i] for i in TOTAL_B5) <= (1-df_investor_targets.loc['B5'].fha_pct_min) * pulp.lpSum(TOTAL_B5[i] * b5_integer[i] for i in TOTAL_B5)


    # Constraints for TOTAL_POOL_CD_UPB
    prob += pulp.lpSum(TOTAL_POOL_CD_UPB[i] * b2_integer[i] for i in TOTAL_B1_UPB) <= df_investor_targets.loc['B2'].longer_dq_pct_max * pulp.lpSum(TOTAL_B1_UPB[i] * b2_integer[i] for i in TOTAL_B1_UPB)
    prob += pulp.lpSum(TOTAL_POOL_CD_UPB[i] * b1_integer[i] for i in TOTAL_B1_UPB) <= df_investor_targets.loc['B1'].longer_dq_pct_max * pulp.lpSum(TOTAL_B1_UPB[i] * b1_integer[i] for i in TOTAL_B1_UPB)

    # Constraints for WA_DQ
    prob += pulp.lpSum(WA_DQ[i] * b4_integer[i] for i in TOTAL_B4) <= df_investor_targets.loc['B4'].dq_months * pulp.lpSum(TOTAL_B4[i] * b4_integer[i] for i in TOTAL_B4)


    # Constraints for APOLLO POOL 1 and POOL 2 relative SIZE 
    prob += pulp.lpSum(TOTAL_B6[i] * b6_integer[i] for i in loan_list) >= df_investor_targets.loc['B6'].b6_pool1_pct_min * pulp.lpSum((TOTAL_B6[i] * b6_integer[i] + TOTAL_B8[i] * b8_integer[i]) for i in loan_list) 


    # Constraints for not double-allocating 
    for i in loan_list:
        prob += b1_integer[i] + b2_integer[i] + b7_integer[i] + b3_integer[i] + b4_integer[i] + b6_integer[i] + b8_integer[i] + b5_integer[i] <= 1
    
    
    # Constraints for profit for each investor  
    for i in loan_list:
        prob += NEC_B1[i]*b1_integer[i] >=0
        prob += NEC_B2[i]*b2_integer[i] >=0
        prob += NEC_B3[i]*b3_integer[i] >=0 
        prob += NEC_B7[i]*b7_integer[i] >=0
        prob += NEC_B4[i]*b4_integer[i] >=0 
        prob += NEC_B6[i]*b6_integer[i] >=0 
        prob += NEC_B8[i]*b8_integer[i] >=0 
        prob += NEC_B5[i]*b5_integer[i] >=0 
    
        
    # EXPORT THE PULP OUTPUT
    # WRITE LP PROBLEM TO A FILE # The problem data is written to an .lp file
    prob.writeLP(optimizer_input_path + '\\Optimize_prob_data.lp')
    
    print('Solving Problem')
    # SOLVE THE OPTIMIZATION
    # SET TIME LIMIT FOR RUNTIME (constant of 3600 seconds = 60 seconds x 60 minutes)
    # number_of_hours = 1
    # prob.solve(pulp.apis.GLPK_CMD(timeLimit=3600 * number_of_hours))
    prob.solve(pulp.apis.GLPK_CMD(timeLimit=1200))

    print("Status: ",pulp.LpStatus[prob.status]) 
    
    
    # POPULATE THE RESULTS FOR EACH VARIABLE INTO LISTS
    print('Prepping Results for CSV')

    mylist = []
    myvalue = []
    myvalue_orig_var = []
    
    
    for variable in prob.variables():
        mylist.append(variable.name[-10:])
        myvalue.append(variable.varValue)
        myvalue_orig_var.append(variable.name)
    
    
    # INSERT THE VARIABLE LIST RESULTS INTO DATAFRAMES
    # import pandas as pd # already imported the pandas library above
    
    df_sol = pd.DataFrame({'LoanId': mylist,
                                  'Flag': myvalue,
                                  'Original_Variable': myvalue_orig_var})
    
    df_sol.set_index('LoanId', inplace=True)
    df_sol.to_csv(optimizer_input_path + '\\Optimizer_solution_loannums.csv') 
    


def get_optimizer_file(): 
    # cwd = os.getcwd()
    cwd = r'C:\Users\jboyce\Desktop\Optimizer Local'
    # MAYBE ADD SET_OPTIMIZER_PATH
    # optimizer_input_path = r'M:\Capital Markets\PIPE\EBO\Optimizer'  # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    optimizer_input_path = cwd # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    optimizer_filename = 'optimizer_input.xlsx' # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    optimizer_pathandfile = optimizer_input_path + '\\' + optimizer_filename
    df = pd.read_excel(optimizer_pathandfile).fillna(0, downcast='infer').set_index('LoanId') #.index.astype('int32') #(np.str)
    #df = df.index.astype(np.str)
    return df



def get_optimizer_results(): 
    """
    This function gets the results output from original optimizer runs
    Creates a dataframe of all loans allocated to Investors
    Then sets Investor allocation columns to 1 if allocated
    
    USER NOTES:
        Change list_investor to include Investor Selectors defined in the variables section of the Optimizer script
        String format is usually INV_Selector so use each INV in the list
        Some examples are B1_Selector, B7_Selector
        list_investor items have to have two initials (e.g., 'B1', 'B7', 'B5')
    """
    list_investor=['B1', 'B2', 'B3', 'B7', 'B4', 'B6', 'B8', 'B5']
    # cwd = os.getcwd()
    cwd = r'C:\Users\jboyce\Desktop\Optimizer Local'
    optimizer_input_path = cwd 
    optimizer_results = 'Optimizer_solution_loannums.csv'
    optimizer_pathandfile = optimizer_input_path + '\\' + optimizer_results
    #df = pd.read_excel(optimizer_pathandfile).set_index('LoanId')
    df = pd.read_csv(optimizer_pathandfile)
    df_opt_input = get_optimizer_file()
    
    #merge it here
    
    # set allocation flags for each Investor
    for item in list_investor:
        df.loc[((df['Original_Variable'].str.contains(item)) & (df['Flag'] == 1)), (item +'_ALLOCATION')] = 1 
        
    #& df_opt['FLAG' + item] == 1
    # create the final dataframe with just the allocated loans
    df = df.loc[df['Flag'] == 1].fillna(0, downcast='infer').set_index('LoanId')
    df.index = df.index.astype('int64') #.index.astype('int32') #(np.str)
    
    df_merged = pd.merge(df_opt_input, df, on = "LoanId", how='left').fillna(0, downcast='infer')
    
    for item in list_investor:
        df_merged.loc[((df_merged['FLAG_' + item] == 0) & (df_merged[item +'_ALLOCATION'] == 1)), (item +'_ALLOCATION')] = 0
        
    df_merged.to_csv(cwd + '\\' + 'df_opt_merged_results.csv') # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    #remove __dummy row
    #df.loc[df['Original_Variable'] == '__dummy'].drop
    
    #dataframe[c] = df['Original_Variable'].str.contains(item)dataframe[c].astype('float32')
    
    return df_merged

def time_string_util(elapsed_time):
    return str(int(round(elapsed_time/60,0))) + " minutes " + str(round(elapsed_time % 60,1)) + " seconds"


def define_investor_targets():
    df = import_df_from_file('investor_initials')
    return df
    

def import_df_from_file(column_for_index=r'LoanId', my_filename=r'config_investor_targets.xlsx', my_filepath=r'M:\Capital Markets\PIPE\EBO\Import'):
    """
    There are three parameters for this import function
    1) Column name to use for index
    2) Filename, including the xlsx or csv extension
    3) Path where the file resides
    """
    if my_filename[-3:] == 'csv':
        df = pd.read_csv(my_filepath + '\\' + my_filename).set_index(column_for_index)
    else:
        df = pd.read_excel(my_filepath + '\\' + my_filename).set_index(column_for_index)
        
    return df     
    



if __name__ == "__main__":
    main()
    
