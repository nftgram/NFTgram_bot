from aiogram.utils.callback_data import CallbackData

edit_token_step = CallbackData("edit_token_step", "step")
approve_token = CallbackData("approve_token", "token_id")
reject_token = CallbackData("reject_token", "token_id")
request_token_changes = CallbackData("request_token_changes", "token_id")
start_changes = CallbackData("start_changes", "token_id")
