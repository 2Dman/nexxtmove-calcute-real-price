# nexxtmove-calcute-real-price
The script reads an Excel export of charging sessions and splits the duration of each session into **day hours** and **night hours**, with **weekend logic**. Based on this, it proportionally allocates the consumption (kWh) to day/night and calculates the **cost in euro cents** using separate day and night tariff prices.
