## Backwards compatibility

Do not keep backwards compatibility or legacy behavior unless I explicitly ask
for it. When a change renames, removes or changes a setting, option, function,
output field or file format, replace the old form outright. Do not add aliases,
deprecation warnings, migrations, fallbacks for old files, or defaults that
exist only so that older files or calls keep working. Keeping older files or
calls working is not a reason to choose or reject a design. Data, outputs and
calls made by an earlier version may stop working. If compatibility looks truly
necessary, ask me first. List what stops working under Risks so I can see it,
rather than designing around it.
