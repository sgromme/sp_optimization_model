import pulp
import pandas as pd

class SupplyPlanningModel:
    def __init__(self):
        """Initialize the supply planning optimization model."""
        self.model = pulp.LpProblem("Supply_Planning_Optimization", pulp.LpMinimize)
        self.periods = []
        self.products = []
        self.variables = {}
        
    def add_products(self, products):
        """Add products to the model."""
        self.products = products
        
    def add_periods(self, periods):
        """Add planning periods to the model."""
        self.periods = periods
        
    def setup_variables(self, initial_inventory=None):
        """Set up decision variables for production, inventory, and backlog."""
        if initial_inventory is None:
            initial_inventory = {p: 0 for p in self.products}
            
        # Production variables
        self.variables['production'] = pulp.LpVariable.dicts(
            "production",
            ((p, t) for p in self.products for t in self.periods),
            lowBound=0
        )
        
        # Inventory variables
        self.variables['inventory'] = pulp.LpVariable.dicts(
            "inventory",
            ((p, t) for p in self.products for t in self.periods),
            lowBound=0
        )
        
        # Backlog variables
        self.variables['backlog'] = pulp.LpVariable.dicts(
            "backlog",
            ((p, t) for p in self.products for t in self.periods),
            lowBound=0
        )
        
        self.initial_inventory = initial_inventory
        
    def add_demand_constraints(self, demand):
        """Add demand satisfaction constraints."""
        for p in self.products:
            for t in self.periods:
                if t == self.periods[0]:
                    # First period considers initial inventory
                    self.model += (
                        self.initial_inventory[p] +
                        self.variables['production'][p,t] -
                        self.variables['inventory'][p,t] +
                        self.variables['backlog'][p,t] == demand[p][t]
                    )
                else:
                    # Other periods consider previous period's inventory
                    self.model += (
                        self.variables['inventory'][p,t-1] +
                        self.variables['production'][p,t] -
                        self.variables['inventory'][p,t] +
                        self.variables['backlog'][p,t] -
                        self.variables['backlog'][p,t-1] == demand[p][t]
                    )
                    
    def add_capacity_constraints(self, capacity_per_period):
        """Add production capacity constraints."""
        for t in self.periods:
            self.model += (
                pulp.lpSum(self.variables['production'][p,t] for p in self.products) 
                <= capacity_per_period
            )
            
    def set_objective(self, production_cost, inventory_cost, backlog_cost):
        """Set the objective function to minimize total costs."""
        self.model += (
            # Production costs
            pulp.lpSum(production_cost[p] * self.variables['production'][p,t]
                      for p in self.products for t in self.periods) +
            # Inventory holding costs
            pulp.lpSum(inventory_cost[p] * self.variables['inventory'][p,t]
                      for p in self.products for t in self.periods) +
            # Backlog costs
            pulp.lpSum(backlog_cost[p] * self.variables['backlog'][p,t]
                      for p in self.products for t in self.periods)
        )
        
    def solve(self):
        """Solve the optimization model."""
        self.model.solve()
        
    def get_results(self):
        """Get the optimization results as a pandas DataFrame."""
        results = {
            'production': {(p,t): self.variables['production'][p,t].value()
                         for p in self.products for t in self.periods},
            'inventory': {(p,t): self.variables['inventory'][p,t].value()
                        for p in self.products for t in self.periods},
            'backlog': {(p,t): self.variables['backlog'][p,t].value()
                       for p in self.products for t in self.periods}
        }
        
        return pd.DataFrame([
            {'product': p,
             'period': t,
             'production': results['production'][p,t],
             'inventory': results['inventory'][p,t],
             'backlog': results['backlog'][p,t]}
            for p in self.products
            for t in self.periods
        ])
    

    # Example usage
model = SupplyPlanningModel()

# Define products and periods
products = ['ProductA', 'ProductB']
periods = list(range(4))  # 4 planning periods
model.add_products(products)
model.add_periods(periods)

# Setup variables with initial inventory
initial_inventory = {'ProductA': 100, 'ProductB': 50}
model.setup_variables(initial_inventory)

# Define demand for each product and period
demand = {
    'ProductA': {0: 120, 1: 140, 2: 160, 3: 130},
    'ProductB': {0: 80, 1: 90, 2: 110, 3: 100}
}
model.add_demand_constraints(demand)

# Add capacity constraints
model.add_capacity_constraints(capacity_per_period=300)

# Define costs
production_cost = {'ProductA': 10, 'ProductB': 12}
inventory_cost = {'ProductA': 2, 'ProductB': 2}
backlog_cost = {'ProductA': 20, 'ProductB': 20}
model.set_objective(production_cost, inventory_cost, backlog_cost)

# Solve and get results
model.solve()
results = model.get_results()
print(results)