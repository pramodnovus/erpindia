from datetime import datetime, timedelta

# Define the duration
#duration_str = "2 16:00:00"
duration_str = "10 23:27:00"


# Parse the duration string
days, time = duration_str.split()
days = int(days)
hours, minutes, seconds = map(int, time.split(':'))

# Create a timedelta object with the parsed values
duration = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

# Get the current date and time
current_datetime = datetime.now()

# Calculate the date and time after the duration
end_datetime = current_datetime + duration

# Calculate the remaining days
remaining_days = (end_datetime - current_datetime).days

print("Remaining days:", remaining_days)