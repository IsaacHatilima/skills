1. Agents have a reference of domain-driver, this sould be used as an example or removed completely and js apps will use domain-driver while laravel apps will use laracanon
2. skills/frontend/dashboard-design/SKILL seems to lean more towards tables and not the whole dashboard like is there a dialog? how is it triggered? does the header move on scroll etc. Skills should not lean towards 1 item but cover the whole issue being addressed. For example on login should rounte be /home, /dashboard or just /, should the backgroung sidebar and body be the same colour?
3. Laravel->actions: it says app/Actions/** but us should say something like if projects uses actions then that, if it uses services use that. Results and failure says: Writes return the model, deletes return `void`, and checks return `bool`. what of cases where it returns a dto? get model and pass it to out bound dto for fomating and other manipulatioins? also file names should have a surffix of what the file is e.g CreateUserAction not CreateUser
4. laravel-insights should tell agents to follow the set rules and not change the files
5. all files that need to should use php attributes this should be reflected in the laravel skills refer to https://github.com/dev-null-sh/dev-null.sh/blob/production/app/Jobs/DetectCommitLanguage.php
6. laravel-phpstan should tell agents to follow the set rules and not change the files
7. laravel-plan is not a laravel skill but all projects and that is covered by spec-writer agent so this should not exist 
8. laravel->testing: as any other stack, when a feature is done, test should only run on the affected files/flows not the whole suit. adding a comment section should not trigger testing change password.
9. nest->data: it does not talk about data(dto) but things like service class and other things. all nest skills need serious review
10. the one next js skill is also bloated. The action skill should only talk about actions in next js
11. tanstack skill also bloated