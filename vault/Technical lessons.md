# Technical lessons

What broke or cost a lot, and how not to repeat it. One bullet each, with date and evidence. Back to [[Lessons]].

- **Never write times by eye**: take every timestamp from the clock (`date -u`).
- **Edit code with the editor tool, not with a script inside a heredoc**: escaped newlines become real ones and the file stops compiling. Always run a syntax check after touching a script.
