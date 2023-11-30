import streamlit as st
import pandas as pd
from pyomo.environ import *
from datetime import datetime

# Function to solve the optimization problem
def solve_optimization(monthly_demand, max_days, capacity):
    model = ConcreteModel()
    
    # Extract product types and lead times from input data
    product_types = list(monthly_demand.keys())
    num_days = max(max_days.values()) + 1
    
    # Variables
    model.production = Var(product_types, range(1, num_days), domain=NonNegativeReals)

    # Constraints
    model.capacity_constraint = Constraint(range(1, num_days), rule=lambda model, day: sum(model.production[ptype, day] for ptype in product_types) <= capacity)
    model.demand_constraint = Constraint(product_types, rule=lambda model, ptype: sum(model.production[ptype, day] for day in range(1, num_days)) >= monthly_demand[ptype])

    # Additional constraint to ensure products are finished within lead times
    model.finish_constraint = Constraint(product_types, rule=lambda model, ptype: sum(model.production[ptype, day] for day in range(1, max_days[ptype] + 1)) >= monthly_demand[ptype])

    # #Solve the optimization problem using GLPK solver
    # #Specify the path to the GLPK solver executable
    # glpk_solver_path = "./glpk/w64/glpsol"
    
    # solver = SolverFactory('glpk', executable=glpk_solver_path) #non active
    solver = SolverFactory('glpk')
    
    result = solver.solve(model)

    # Check the solver status
    if result.solver.termination_condition == TerminationCondition.optimal:
        st.success("Optimal solution found!")

        # Store the output in a Pandas DataFrame
        output_data = {'Product_Type': product_types}

        for day in range(1, num_days):
            output_data[f'Day_{day}'] = [model.production[ptype, day]() for ptype in product_types]

        output_df = pd.DataFrame(output_data)
        st.dataframe(output_df)

        # Return the DataFrame for download
        return output_df

    else:
        st.warning("Solver did not find an optimal solution. Check your constraints.")
        return None

# Streamlit App
st.title("Production Scheduler")

# Upload CSV file for monthly_demand and max_days
uploaded_file = st.file_uploader("Upload CSV monthly_demand File", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    monthly_demand = dict(zip(df['Product_Type'], df['Monthly_Demand']))
    max_days = dict(zip(df['Product_Type'], df['Max_Days']))

    st.write("Monthly Demand and Max Days:")
    st.write(df)

    # Input box for capacity
    capacity = st.number_input("Enter Capacity:", min_value=400)

    # Button to create schedule
    if st.button("Create Schedule"):
        output_df = solve_optimization(monthly_demand, max_days, capacity)

        # Download button for the resulting DataFrame
        if output_df is not None:
         # Include today's date in the file name
            today_date = datetime.today().strftime('%d-%b-%y')
            file_name = f"prod_plan_{today_date}.csv"
            
            st.download_button(
                label="Download Schedule",
                data=output_df.to_csv(index=False).encode('utf-8-sig'),  # Encoding correction
                file_name= file_name,
                key="download_button"
            )
