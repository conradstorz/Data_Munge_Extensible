from whenever import Instant,ZonedDateTime,LocalDateTime

# Identify moments in time, without timezone/calendar complexity
now = Instant.now()
print (now)  # example 2024-07-17T13:35:10.3704526Z

# Simple, explicit conversions
new_tz = now.to_tz("Europe/Paris")
print (new_tz)  # example 2024-07-17T15:37:03.7656869+02:00[Europe/Paris]

# A 'naive' local time can't accidentally mix with other types.
# You need to explicitly convert it and handle ambiguity.
party_invite = LocalDateTime(2023, 10, 28, hour=22)
try:
    party_invite.add(hours=6)
    # example of error:
    """Adding time units to a LocalDateTime implicitly ignores Daylight Saving Time. 
    Instead, convert to a ZonedDateTime first using assume_tz(). 
    Or, if you're sure you want to ignore DST, explicitly pass ignore_dst=True."""
except Exception as e:
   print (e)

party_starts = party_invite.assume_tz("Europe/Amsterdam", disambiguate="earlier")
print (party_starts)  # example 2023-10-28T22:00:00+02:00[Europe/Amsterdam]

# DST-safe arithmetic
party_starts.add(hours=6)
print(party_starts)  # example 2023-10-28T22:00:00+02:00[Europe/Amsterdam]

# Comparison and equality
print(f'is now greater than "Party_starts"? {now > party_starts}')

# Formatting & parsing common formats (ISO8601, RFC3339, RFC2822)
print(f'Formatting & parsing common formats (ISO8601, RFC3339, RFC2822): {now.format_rfc2822()}')

# If you must: you can convert to/from the standard lib
print(f'If you must: you can convert to/from the standard lib: {now.py_datetime()}')

"""
datetime.datetime(2024, 7, 4, 10, 36, 56, tzinfo=datetime.timezone.utc)
"""