from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# Constants
node_requirement = 1000000
version = "v1.18"

# Store additional stakes
additional_stakes = []

@app.route('/', methods=['GET', 'POST'])
def index():
    global additional_stakes
    if request.method == 'POST':
        initial_nodes = int(request.form['initial_nodes'])
        neoxa_spot_price = float(request.form['neoxa_spot_price'])
        usd_to_kd = float(request.form['usd_to_kd'])
        neoxa_decimals = int(request.form['neoxa_decimals'])
        usd_decimals = int(request.form['usd_decimals'])
        kd_decimals = int(request.form['kd_decimals'])
        daily_yield_rate = float(request.form['daily_yield_rate'])
        node_yield_per_48h = float(request.form['node_yield_per_48h'])
        start_date = pd.to_datetime(request.form['start_date'])
        initial_stake_amount = float(request.form['initial_stake_amount'])
    else:
        initial_nodes = 1
        neoxa_spot_price = 0.001650  # Default value
        usd_to_kd = 0.310  # Default value
        neoxa_decimals = 0  # Default decimals for Neoxa
        usd_decimals = 2  # Default decimals for USD
        kd_decimals = 3  # Default decimals for KD
        daily_yield_rate = 0.001  # Default daily yield rate
        node_yield_per_48h = 2250  # Default node yield per 48 hours
        start_date = pd.Timestamp('2024-06-09')  # Default start date
        initial_stake_amount = 177000  # Default initial stake amount

    total_months = 60

    # Initial calculations
    initial_stake = initial_stake_amount
    node_yield_48h = node_yield_per_48h * initial_nodes

    # Combine initial and additional stakes
    stakes = [(start_date, initial_stake_amount)]
    stakes.extend(additional_stakes)
    stakes.sort()

    # Create a DataFrame to store results
    columns = [
        "Month", "Month Abbr", "Node Count", "Staked (Neoxa)", "Just Node Yield (Neoxa)",
        "Inodez Yield (Neoxa)", "Total Yield (Neoxa)", "USD Value", "KD Value", "Running Total KD"
    ]
    data = []

    # Initialize state variables
    current_stake = initial_stake
    nodes = initial_nodes
    total_kd = 0

    # Function to calculate daily yield
    def calculate_daily_yield(stake):
        return stake * daily_yield_rate

    # Loop through each month
    for month in range(total_months):
        # Determine the number of days in the current month
        current_date = start_date + pd.DateOffset(months=month)
        days_in_month = current_date.days_in_month
        month_abbr = current_date.strftime('%b')

        # Capture the staked amount at the start of the month AFTER adding stakes 
        staked_at_start_of_month = current_stake
        for stake_date, stake_amount in stakes:
            if current_date - pd.DateOffset(days=days_in_month) <= stake_date <= current_date:
                staked_at_start_of_month += stake_amount

        # Calculate monthly yield and add node yields every 48 hours
        monthly_stake_yield = 0
        node_yield = 0
        inodez_yield = 0
        for day in range(1, days_in_month + 1):
            daily_yield = calculate_daily_yield(current_stake)
            inodez_yield += daily_yield
            monthly_stake_yield += daily_yield
            current_stake += daily_yield

            # Every 48 hours, add node yield
            if day % 2 == 0:
                current_stake += node_yield_48h
                node_yield += node_yield_48h

            # Check if new nodes can be created
            while current_stake >= node_requirement:
                nodes += 1
                current_stake -= node_requirement
                node_yield_48h += node_yield_per_48h  # Update node yield rate

        # Calculate total yield
        total_yield = inodez_yield + node_yield

        # Calculate values in USD and KD
        usd_value = total_yield * neoxa_spot_price
        kd_value = usd_value * usd_to_kd
        total_kd += kd_value

        # Append data for the current month
        data.append([
            month + 1, month_abbr, nodes, 
            f"{staked_at_start_of_month:,.{neoxa_decimals}f}", 
            f"{node_yield:,.{neoxa_decimals}f}", 
            f"{inodez_yield:,.{neoxa_decimals}f}", 
            f"{total_yield:,.{neoxa_decimals}f}", 
            f"{usd_value:,.{usd_decimals}f}", 
            f"{kd_value:,.{kd_decimals}f}", 
            f"{total_kd:,.{kd_decimals}f}"
        ])

    # Create a DataFrame from the data
    df = pd.DataFrame(data, columns=columns)
    table_html = df.to_html(classes='table table-striped', index=False, justify='center', table_id='resultsTable')

    return render_template('index.html', table=table_html, version=version, neoxa_spot_price=neoxa_spot_price, usd_to_kd=usd_to_kd, initial_nodes=initial_nodes, neoxa_decimals=neoxa_decimals, usd_decimals=usd_decimals, kd_decimals=kd_decimals, daily_yield_rate=daily_yield_rate, node_yield_per_48h=node_yield_per_48h, start_date=start_date.strftime('%Y-%m-%d'), initial_stake_amount=initial_stake_amount)


# ... (rest of the routes: /add-stake and /stake-log)

if __name__ == '__main__':
    app.run(debug=True)
