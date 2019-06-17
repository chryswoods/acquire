
Acquire.Login = {};

Acquire.Login._panels = {};
Acquire.Login._handles = {};
Acquire.Login._forms = {};
Acquire.Login._reminders = {};
Acquire.Login._progress = {};

/** Function to switch the display to a specific panel */
Acquire.Login.show_panel = function(panel)
{
    Object.keys(Acquire.Login._panels).forEach(function(key)
    {
        let p = Acquire.Login._panels[key];

        if (p)
        {
            if (key == panel)
            {
                p.style.display = "inline";
            }
            else
            {
                p.style.display = "none";
            }
        }
    });
}

/** Function to set and display progress */
Acquire.Login.set_progress = function(text, percent)
{
    let label = Acquire.Login._progress["label"];
    let bar = Acquire.Login._progress["bar"];
    let panel = Acquire.Login._panels["progress"];

    if (!panel){ return;}

    if (label)
    {
        label.textContent = text;
    }

    if (bar)
    {
        let width = percent;
        if (width < 0)
        {
            width = 0;
        }
        else if (width > 100)
        {
            width = 100;
        }

        bar.style.width = width + '%';
        bar.innerHTML = width * 1 + '%';
   }

   Acquire.Login.show_panel("progress");
}

/** Show the failure page - if 'detail' is an exception this will
 *  try to get the most useful human-meaningful error message
 *  that can be quickly displayed
 */
Acquire.Login.show_fail = function(message, detail=undefined)
{
    let label = document.getElementById("acquire.fail.header");

    if (label)
    {
        label.textContent = message;
    }

    label = document.getElementById("acquire.fail.message");

    if (detail)
    {
        while (detail.cause)
        {
            detail = detail.cause;
        }

        if (detail.error)
        {
            detail = detail.error;
        }
    }
    if (label && detail)
    {
        label.textContent = `${detail}`;
    }

    Acquire.Login.show_panel("fail");
}

Acquire.Login.show_success = function(message, detail=undefined)
{
    let label = document.getElementById("acquire.success.header");

    if (label)
    {
        label.textContent = message;
    }

    label = document.getElementById("acquire.success.message");

    if (label && detail)
    {
        label.textContent = detail;
    }

    Acquire.Login.show_panel("success");
}

Acquire.Login.restart = function()
{
    Acquire.Login.show_panel("url");
}

/** Function used to show the username/password page */
Acquire.Login.show_user_password = function(message)
{
    if (!Acquire.Login._identity_service)
    {
        return;
    }

    let service = Acquire.Login._identity_service;
    let short_uid = Acquire.Login._short_uid;

    let header = document.getElementById("acquire.userpassword.header");
    let m = document.getElementById("acquire.userpassword.message");

    if (header)
    {
        let canon = service.canonical_url();
        let serv = service.service_url();
        header.innerHTML = `Logging onto <a href="${serv}">${canon}</a>`;
    }

    if (m)
    {
        if (message)
        {
            m.textContent = `Session ${short_uid}. Login message '${message}'`;
        }
        else
        {
            m.textContent = `Session ${short_uid}`;
        }
    }

    Acquire.Login.show_panel("userpassword");
}

/** Function used to complete the login */
Acquire.Login.complete_login = async function(wallet, otpcode=undefined,
                                              remember_device=false)
{
    let service = Acquire.Login._identity_service;
    let short_uid = Acquire.Login._short_uid;
    let username = Acquire.Login._username;
    let password = Acquire.Login._password;

    try
    {
        await wallet.send_password({service:service,
                                    short_uid:short_uid,
                                    username:username,
                                    password:password,
                                    otpcode:otpcode,
                                    remember_device:remember_device});
    }
    catch(err)
    {
        console.log(err);
        let obj = JSON.parse(JSON.stringify(err));
        console.log(obj);

        Acquire.Login.show_fail(`Unable to to log in!`, err);
        return;
    }

    Acquire.Login.show_success("Login successful!");
}

/** Function used to handle submission of a user otpcode */
Acquire.Login.submit_otp = async function (wallet, otpcode, remember_device)
{
    Acquire.Login.set_progress("Submitting credentials...", 50);
    Acquire.Login.complete_login(wallet, otpcode, remember_device)
}

/** Function used to submit the username and password */
Acquire.Login.submit_userpassword = async function(wallet, username, password)
{
    Acquire.Login.set_progress("Submitting credentials...", 50);
    let service = Acquire.Login._identity_service;

    if (!service)
    {
        return;
    }

    Acquire.Login._username = username;
    Acquire.Login._password = password;

    try
    {
        //try to complete the login - this will use a saved device
        //otpcode if possible
        let short_uid = Acquire.Login._short_uid;

        await wallet.send_password({service:service,
                                    short_uid:short_uid,
                                    username:username,
                                    password:password,
                                    otpcode:undefined,
                                    remember_device:false});

        Acquire.Login.show_success("Login successful!");
        return;
    }
    catch(_err)
    {
        console.log("Failed login with wallet-based otpcode...");
        console.log(_err);
    }

    //this failed because either the user doesn't have an otpcode
    //or because something was wrong with the old otpcode. Ask
    //the user for a manual otpcode
    Acquire.Login.show_panel("otpcode");
}

/** Function used to submit the login URL and kick-off the process
 *  of logging in
 */
Acquire.Login.submit_url = async function(wallet, service_uid, short_uid)
{
    let registry, service, message = undefined;

    try
    {
        Acquire.Login.set_progress("Connecting to registry service...", 25);
        registry = await wallet._get_trusted_registry_service();
    }
    catch(err)
    {
        console.log(err);
        Acquire.Login.show_fail("Could not connect to the registry service!",
                                err);
        return;
    }

    try
    {
        Acquire.Login.set_progress("Connecting to login service...", 50);
        service = await wallet.get_service({service_uid:service_uid});
    }
    catch(err)
    {
        console.log(err);
        Acquire.Login.show_fail("Could not connect to the login service!",
                                err);
        return;
    }

    try
    {
        Acquire.Login.set_progress("Getting session info...", 75);
        let args = {"short_uid":short_uid,
                    "status":"pending"};
        let result = await service.call_function({func:"get_session_info",
                                                  args:args});
        message = result["login_message"];
    }
    catch(err)
    {
        console.log(err);
        Acquire.Login.show_fail("Could not get the login session info!",
                                err);
        return
    }

    //save the service and short_uid
    Acquire.Login._identity_service = service;
    Acquire.Login._short_uid = short_uid;

    //now switch to the username/password page
    Acquire.Login.show_user_password(message);
}

Acquire.Login.initialise = async function()
{
    // create a Wallet which will be used for the login
    let wallet = new Acquire.Wallet();

    let panels = ["url", "userpassword", "otpcode", "success",
                  "fail", "progress"];

    /* Find all of the panels in the html page and initially set them
       as invisible. Also locate all of the forms and all of the reminders */
    panels.forEach(function(panel)
    {
        let panel_element = document.getElementById(`acquire.${panel}.panel`);
        panel_element.style.display = "none";
        Acquire.Login._panels[panel] = panel_element;

        let form_element = document.getElementById(`acquire.${panel}.form`);

        if (form_element)
        {
            Acquire.Login._forms[panel] = form_element;
        }
    });

    // now find all of the reminder elements
    let reminders = ["url", "username", "password", "otpcode"];

    reminders.forEach(function(reminder)
    {
        let reminder_element = document.getElementById(
                                            `acquire.${reminder}.reminder`);

        if (reminder_element)
        {
            Acquire.Login._reminders[reminder] = reminder_element;

            //make sure that the reminder is initially invisible
            reminder_element.style.display = "none";
        }
    });

    // now create all of the form handlers
    let handle_url_form = async function(event)
    {
        let form = Acquire.Login._forms["url"];
        let data = Acquire.Form.getFormSubmitData(form, event);

        let url = data["url"];

        if (url)
        {
            let service_uid, short_uid = undefined;

            try
            {
                [service_uid, short_uid] =
                            Acquire.Wallet.get_login_details_from_url(url);
            }
            catch(_err)
            {}

            let reminder = Acquire.Login._reminders["url"];

            if (service_uid)
            {
                if (reminder)
                {
                    reminder.style.display = "none";
                }

                Acquire.Login.submit_url(wallet, service_uid, short_uid);
            }
            else
            {
                if (reminder)
                {
                    reminder.textContent = "This should " +
                      "have the form " +
                      "https://login.acquire-aaai.com?id=XX-YY/ZZ.ZZ.ZZ.ZZ";

                    reminder.style.display = "inline";
                }
            }
        }
    }
    Acquire.Login._handles["url"] = handle_url_form;

    let handle_userpassword_form = async function(event)
    {
        let form = Acquire.Login._forms["userpassword"];
        let data = Acquire.Form.getFormSubmitData(form, event);

        let remind_username = Acquire.Login._reminders["username"];
        let remind_password = Acquire.Login._reminders["password"];

        let username = data["username"];
        let password = data["password"];
        let ok = true;

        if (username)
        {
            if (remind_username){ remind_username.style.display = "none";}
        }
        else
        {
            if (remind_username){ remind_username.style.display = "inline";}
            ok = false;
        }

        if (password)
        {
            if (remind_password){ remind_password.style.display = "none";}
        }
        else
        {
            if (remind_password){ remind_password.style.display = "inline";}
            ok = false;
        }

        if (!ok){ return;}

        await Acquire.Login.submit_userpassword(wallet, username, password);
    }
    Acquire.Login._handles["userpassword"] = handle_userpassword_form;

    let handle_otpcode_form = async function(event)
    {
        let form = Acquire.Login._forms["otpcode"];
        let data = Acquire.Form.getFormSubmitData(form, event);

        let remind_input = Acquire.Login._reminders["otpcode"];

        let otpcode = data["otpcode"];
        let remember_device = data["remember_device"];

        if (otpcode)
        {
            if (remind_input){ remind_input.style.display = "none"; }
        }
        else
        {
            if (remind_input){ remind_input.style.display = "inline"; }
            return;
        }

        await Acquire.Login.submit_otp(wallet, otpcode, remember_device);
    }
    Acquire.Login._handles["otpcode"] = handle_otpcode_form;

    let handle_success_form = async function(event)
    {
        let form = Acquire.Login._forms["success"];
        let data = Acquire.Form.getFormSubmitData(form, event);
        Acquire.Login.restart();
    }
    Acquire.Login._handles["success"] = handle_success_form;

    let handle_fail_form = async function(event)
    {
        let form = Acquire.Login._forms["fail"];
        let data = Acquire.Form.getFormSubmitData(form, event);
        Acquire.Login.restart();
    }
    Acquire.Login._handles["fail"] = handle_fail_form;

    let handle_progress_form = async function(event)
    {
        let form = Acquire.Login._forms["progress"];
        let data = Acquire.Form.getFormSubmitData(form, event);
        Acquire.Login.restart();
    }
    Acquire.Login._handles["progress"] = handle_progress_form;

    // associate all of the form "submit" handlers with the forms
    Object.keys(Acquire.Login._handles).forEach(function(key)
    {
        try
        {
            Acquire.Login._forms[key].addEventListener(
                                    "submit", Acquire.Login._handles[key]);
        }
        catch(err)
        {
            console.log(`ERROR ADDING EVENT LISTENER FOR FORM ${key}`);
            console.log(err);
        }
    });

    Acquire.Login._progress["bar"] = document.getElementById(
                                                "acquire.progress.bar");
    Acquire.Login._progress["label"] = document.getElementById(
                                                "acquire.progress.label");

    // see if we can extract the login ID from our URL...
    let url = window.location.href;
    let service_uid, short_uid = undefined;

    try
    {
        [service_uid, short_uid] =
                    Acquire.Wallet.get_login_details_from_url(url);
    }
    catch(_err)
    {}

    if (service_uid)
    {
        await Acquire.Login.submit_url(wallet, service_uid, short_uid);
    }
    else
    {
        Acquire.Login.show_panel("url");
    }
}
