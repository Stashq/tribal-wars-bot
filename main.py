from bot import Bot

sc_bot = Bot(prevent=True, safe_mode=False, allow_time_reducing=True, pp_limit=1000)
sc_bot.run()