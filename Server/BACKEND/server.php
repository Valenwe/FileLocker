<?php
require("functions.php");

if (session_id() == null)
    session_start();

$errors = array();

// PREVENT XSS
foreach ($_POST as $val => $key) {
    $_POST[$val] = strip_tags($key);
}

// ~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=
// ~=~= ACCOUNT CREATION & LOGIN ~=~=~=
// ~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=

// LOGIN USER
if (isset($_POST['log_user'])) {
    $username = $_POST['log_username'];
    $password = $_POST['log_password'];

    if (empty($username))
        array_push($errors, "Username is required");

    if (empty($password))
        array_push($errors, "Password is required");

    if (count($errors) == 0) {
        $user = find("users", array("username" => $username), 1);
        if ($user && password_verify($password, $user['password'])) {
            if (!empty($user["a2f_code"])) {
                // TOTP verification
                if (!isOTPvalid($_POST['log_otp_code'], $user["a2f_code"]))
                    array_push($errors, "Wrong double authentication code");
            } else
                array_push($errors, "Double authentication code is required");


            if (count($errors) == 0) {
                $ask_key = $_POST["ask_key"];
                set_session_value($user);
                echo $user["id_user"];

                if ($ask_key == "1") {
                    echo " ~~~ " . $user["cipher_private_key"];
                }
            }
        } else {
            array_push($errors, "Wrong username/password combination");
        }
    }
    goto end;
}

// REGISTER USER
if (isset($_POST['reg_user'])) {
    // form validation: ensure that the form is correctly filled ...
    // by adding (array_push()) corresponding error unto $errors array
    if (empty($_POST['reg_username']))
        array_push($errors, "Username is required");

    if (empty($_POST['reg_email']))
        array_push($errors, "Email is required");

    if (empty($_POST['reg_password_1']) || empty($_POST['reg_password_2']))
        array_push($errors, "Password is required");


    if (count($errors) == 0) {
        // receive all input values from the form
        $username = $_POST['reg_username'];
        $email = $_POST['reg_email'];
        $password_1 = $_POST['reg_password_1'];
        $password_2 = $_POST['reg_password_2'];

        if (!is_str_valid($username))
            array_push($errors, "Invalid username (characters allowed are letters, numbers and '_')");

        if (strlen($password_1) <= 5)
            array_push($errors, "The password has to be at least 6 characters long");

        if (!preg_match('~[0-9]+~', $password_1))
            array_push($errors, "The password must contain at least one digit number");

        if ($password_1 != $password_2)
            array_push($errors, "The two passwords do not match");

        $user = find("users", array("username" => $username), 1, array("username", "email"));
        if ($user)
            array_push($errors, "Username already exists");

        $user = find("users", array("email" => $email), 1, array("username", "email"));
        if ($user)
            array_push($errors, "Email already exists");


        if (count($errors) == 0) {
            // Bcrypt algorithm
            $password = password_hash($password_1, PASSWORD_BCRYPT);

            $new_user = array("username" => $username, "email" => $email, "password" => $password);

            // generating encryption environnement
            $backup_code = generate_random_name();

            $key_pair = generate_key_pair();
            $new_user["public_key"] = (string) $key_pair["public"];
            $new_user["cipher_private_key"] = encryptDataAES((string) $key_pair["private"], $backup_code);

            $a2f = generateTOTPCode();
            $new_user["a2f_code"] = $a2f["secret"];

            // TOTP friend request code
            $new_user["friendrequest_code"] = generateTOTPCode()["secret"];

            create("users", $new_user);
            set_session_value(find("users", array("username" => $username), 1));

            // afficher les backupcode à l'utilisateur pour qu'il les sauvegarde !!
            // afficher a2f url qrcode pour qu'il le sauvegarde !
            $_SESSION["private_passphrase"] = $backup_code;
            $_SESSION["a2f_url"] = $a2f["url"];
            header('location: getQR.php');
        }
    }
    $_SESSION["errors"] = $errors;
    return;
}

// LOG OUT
if (isset($_POST["log_out"])) {
    if (session_id() != null)
        session_unset();
    goto end;
}

// ~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=
// ~=~=     USER MANAGEMENT      ~=~=~=
// ~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=
/*
$_SESSION["username"] = "test";
$_SESSION["id_user"] = 4;
$_POST["fetch_information"] = 1;
*/

// PART WHERE THE USER HAS TO BE CONNECTED
if (!isset($_SESSION["username"])) {
    // echo 0;
    goto end;
}

// FETCH USER INFORMATION
if (isset($_POST["fetch_information"])) {
    $id = addslashes($_SESSION["id_user"]);

    $friend_response = array();
    $friends = special_find_query("SELECT id_user, username, email FROM friends F
    LEFT JOIN users U ON U.id_user = F.id_user_1 OR U.id_user = F.id_user_2
    WHERE (F.id_user_1 = $id OR F.id_user_2 = $id) AND username != '" . $_SESSION["username"] . "'");

    foreach ($friends as $friend) {
        $friend_json = array();
        $friend_json["id"] = $friend["id_user"];
        $friend_json["name"] = $friend["username"];
        $friend_json["email"] = $friend["email"];

        array_push($friend_response, $friend_json);
    }

    $group_response = array();
    $groups = special_find_query("SELECT GU.id_group, G.name as group_name, GU.id_permission, U.id_user, U.username, U.email
    FROM group_user GU LEFT JOIN groups G ON G.id_group = GU.id_group LEFT JOIN users U ON U.id_user = G.owner WHERE GU.id_user = $id");

    foreach ($groups as $group) {
        $group_json = array();
        $group_json["id"] = $group["id_group"];
        $group_json["name"] = $group["group_name"];
        $group_json["id_permission"] = $group["id_permission"];

        $owner = array();
        $owner["id"] = $group["id_user"];
        $owner["name"] = $group["username"];
        $owner["email"] = $group["email"];

        $group_json["owner"] = $owner;

        $files_json = array();
        // only the files that have been ciphered for you will be visible
        $files = special_find_query("SELECT F.path, F.size, F.modification_date, CF.ciphered_aes, CF.ciphered_nonce,
        U.id_user, U.username, U.email
        FROM files F LEFT JOIN ciphered_for CF ON CF.path = F.path AND CF.id_group = F.id_group LEFT JOIN users U ON U.id_user = F.author
        WHERE CF.id_user = $id AND F.id_group = " . $group["id_group"]);

        foreach ($files as $file) {
            $file_json = array();
            $file_json["path"] = $file["path"];
            $file_json["size"] = $file["size"];
            $file_json["ciphered_aes"] = $file["ciphered_aes"];
            $file_json["ciphered_nonce"] = $file["ciphered_nonce"];
            $file_json["modification_date"] = $file["modification_date"];

            $owner = array();
            $owner["id"] = $file["id_user"];
            $owner["name"] = $file["username"];
            $owner["email"] = $file["email"];

            $file_json["owner"] = $owner;

            $all_destinations = array();
            $ciphered_for = special_find_query("SELECT CF.id_user, U.username, U.email
            FROM ciphered_for CF LEFT JOIN users U ON U.id_user = CF.id_user WHERE CF.path = '" . $file["path"] . "' AND CF.id_group = " . $group["id_group"]);

            foreach ($ciphered_for as $cf) {
                $cf_json = array();
                $cf_json["id"] = $cf["id_user"];
                $cf_json["name"] = $cf["username"];
                $cf_json["email"] = $cf["email"];

                array_push($all_destinations, $cf_json);
            }
            $file_json["ciphered_for"] = $all_destinations;

            array_push($files_json, $file_json);
        }
        $group_json["files"] = $files_json;

        $users = special_find_query("SELECT U.id_user, U.username, U.email, U.public_key, GU.id_permission FROM users U
        LEFT JOIN group_user GU ON GU.id_user = U.id_user WHERE GU.id_group = " . $group["id_group"]);
        $users_json = array();

        foreach ($users as $user) {
            $user_json = array();
            $user_json["id"] = $user["id_user"];
            $user_json["name"] = $user["username"];
            $user_json["email"] = $user["email"];
            $user_json["id_permission"] = $user["id_permission"];
            $user_json["public_key"] = $user["public_key"];

            array_push($users_json, $user_json);
        }
        $group_json["users"] = $users_json;

        $group_response[$group_json["id"]] = $group_json;
    }

    $final_json = array();
    $final_json["friends"] = $friend_response;
    $final_json["groups"] = $group_response;

    $final_json["username"] = $_SESSION["username"];
    $final_json["friendrequest_code"] = $_SESSION["friendrequest_code"];

    #header('Content-Type: application/json; charset=utf-8');
    echo json_encode($final_json);
    goto end;
}

// ADD FRIEND
if (isset($_POST["add_friend"])) {
    $friend_name = $_POST["friend_name"];
    $friend_otp_code = $_POST["friend_code"];

    $friend = find("users", array("username" => $friend_name), 1);

    if ($friend == null) { # || $friend_name == $_SESSION["username"]
        array_push($errors, "Selected user doesn't exist");
        echo 502;
        goto end;
    }

    $secret_friend_code = $friend["friendrequest_code"];

    if (!isOTPvalid($friend_otp_code, $secret_friend_code)) {
        array_push($errors, "Selected user did not give a valid OTP code");
        echo 505;
        goto end;
    }

    $current_user = find("users", array("id_user" => $_SESSION["id_user"]), 1);

    $current_user_id = $current_user["id_user"];
    $friend_id = $friend["id_user"];

    $relation = special_find_query("SELECT * FROM friends WHERE (id_user_1 = $current_user_id AND id_user_2 = $friend_id) OR (id_user_2 = $current_user_id AND id_user_1 = $friend_id)");

    if (!$relation) {
        create("friends", array("id_user_1" => $current_user_id, "id_user_2" => $friend_id));
    } else {
        array_push($errors, "Users are already friends");
        echo 503;
        goto end;
    }
}

// REMOVE FRIEND
if (isset($_POST["remove_friend"])) {
    $friend_name = $_POST["friend_name"];

    $friend = find("users", array("username" => $friend_name), 1);

    if ($friend == null) {
        array_push($errors, "Selected user doesn't exist");
        echo 502;

        goto end;
    }

    $current_user = find("users", array("id_user" => $_SESSION["id_user"]), 1);

    $current_user_id = $current_user["id_user"];
    $friend_id = $friend["id_user"];

    $relation1 = special_find_query("SELECT * FROM friends WHERE (id_user_1 = $current_user_id AND id_user_2 = $friend_id)");
    $relation2 = special_find_query("SELECT * FROM friends WHERE (id_user_2 = $current_user_id AND id_user_1 = $friend_id)");

    if ($relation1 == null && $relation2 == null) {
        array_push($errors, "Users are not friends");
        echo 504;
    } else if ($relation1 != null) {
        delete("friends", array("id_user_1" => $current_user_id, "id_user_2" => $friend_id));
    } else {
        delete("friends", array("id_user_2" => $current_user_id, "id_user_1" => $friend_id));
    }
}

//CHANGE PERMISSION
if (isset($_POST["change_permission"])) {
    $id_user = $_SESSION["id_user"];
    $id_group = $_POST["id_group"];

    $group = find("groups", array("id_group" => $id_group), 1);
    $permission = (find("group_user", array("id_user" => $id_user, "id_group" => $id_group), 1))["id_permission"];

    if ($permission == 3) {
        $user_id_to_change = $_POST["user_id_to_change"];

        if ($user_id_to_change == $id_user) {
            array_push($errors, "User cannot change his own permissions");
            echo 807;
            goto end;
        }

        if ($user_id_to_change == $group["owner"]) {
            array_push($errors, "You cannot change the owner's permissions");
            echo 808;
            goto end;
        }

        $found = find("group_user", array("id_user" => $user_id_to_change, "id_group" => $id_group), 1);
        if ($found == null) {
            array_push($errors, "User does not exist");
            echo 802;
            goto end;
        }

        $new_perm = $_POST["new_perm"];

        //Check si c'est le bon format
        if ($new_perm != 1 && $new_perm != 2 && $new_perm != 3) {
            array_push($errors, "Permission is not between 1 and 3");
            echo 804;
            goto end;
        }

        update("group_user", array("id_permission" => $new_perm), array("id_user" => $user_id_to_change, "id_group" => $id_group));
    } else {
        array_push($errors, "User does not have admin permissions");
        echo 803;
    }
}

// ADD USER IN GROUP
if (isset($_POST["add_group_user"])) {
    $id_user = $_SESSION["id_user"];
    $id_group = $_POST["id_group"];

    $permission = (find("group_user", array("id_user" => $id_user, "id_group" => $id_group), 1))["id_permission"];

    if ($permission == 3) {
        $new_user_id = $_POST["new_user_id"];

        //Check si le user existe
        $found = find("users", array("id_user" => $new_user_id), 1);
        if ($found == null) {
            array_push($errors, "User does not exist");
            echo 802;
            goto end;
        }

        //Check si le user est déjà dans le groupe
        $found_in_group = find("group_user", array("id_user" => $new_user_id, "id_group" => $id_group), 1);
        if ($found_in_group) {
            array_push($errors, "User is already in this group");
            echo 801;
            goto end;
        }

        create("group_user", array("id_user" => $new_user_id, "id_group" => $id_group, "id_permission" => 1));
    } else {
        array_push($errors, "User does not have admin permissions");
        echo 803;
        goto end;
    }
}

// REMOVE USER FROM GROUP
if (isset($_POST["remove_group_user"])) {
    $id_user = $_SESSION["id_user"];
    $id_group = $_POST["id_group"];

    $permission = (find("group_user", array("id_user" => $id_user, "id_group" => $id_group), 1))["id_permission"];

    if ($permission == 3) {
        $user_id_del = $_POST["new_user_id"];

        if ($user_id_del == $id_user) {
            array_push($errors, "User cannot change delete him/herself");
            echo 807;
            goto end;
        }

        //Check si le user existe
        $found = find("users", array("id_user" => $user_id_del), 1);
        if ($found == null) {
            array_push($errors, "User does not exist");
            echo 802;
            goto end;
        }

        //Check si le user n'est pas dans le groupe
        $found_in_group = find("group_user", array("id_user" => $user_id_del, "id_group" => $id_group), 1);
        if ($found_in_group == null) {
            array_push($errors, "User is not in this group");
            echo 806;
            goto end;
        }

        delete("group_user", array("id_user" => $user_id_del, "id_group" => $id_group));
        rrmdir("./groups/$id_group/$user_id_del");
    } else {
        array_push($errors, "User does not have admin permissions");
        echo 803;
        goto end;
    }
}

// ~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=
// ~=~=     FILE MANAGEMENT      ~=~=~=
// ~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=

// ADD FILE
if (isset($_POST["add_file"])) {
    $id_group = $_POST["id_group"];
    $wanted_path = $_POST["wanted_path"];
    $filename = $_POST["filename"];

    $ciphered_for = $_POST["ciphered_for"];
    $ciphered_aes = $_POST["ciphered_aes"];
    $ciphered_nonce = $_POST["ciphered_nonce"];

    $permission = (find("group_user", array("id_user" => $_SESSION["id_user"], "id_group" => $id_group), 1))["id_permission"];

    if ($permission == 1) {
        array_push($errors, "You do not have the authorization!");
        echo 504;
        goto end;
    }

    if (strstr($filename, '/') || strstr($filename, '\\') || strstr($filename, '*')) {
        echo 503;
        array_push($errors, "Character unallowed in filename");
        goto end;
    }

    // create all directories not present in user
    $temp_path = "";
    foreach (explode("/", $ciphered_for . "/" . $wanted_path) as $dir) {
        $temp_path .= "/$dir";
        if (!file_exists("./groups/$id_group/$temp_path"))
            mkdir("./groups/$id_group/$temp_path");
    }

    $target_dir = "./groups/$id_group/$ciphered_for/$wanted_path";
    if (isset($_FILES["uploaded_file"])) {
        // $filename = basename($_FILES["uploaded_file"]["name"]);
        $target_file = $target_dir . $filename;

        if (file_exists($target_file) === true) {
            array_push($errors, "File already exists in this folder");
            echo 501;
            goto end;
        }

        if (!(move_uploaded_file($_FILES["uploaded_file"]["tmp_name"], $target_file))) {
            array_push($errors, "File not uploaded");
            echo 502;
            goto end;
        } else {

            $pre_existing_file = find("files", array("path" => $wanted_path . $filename, "id_group" => $id_group), 1);

            if (!$pre_existing_file)
                create("files", array(
                    "id_group" => $id_group, "author" => $_SESSION["id_user"],
                    "size" => filesize($target_dir . $filename), "path" => $wanted_path . $filename
                ));

            create("ciphered_for", array(
                "path" => $wanted_path . $filename, "id_user" => $ciphered_for,
                "id_group" => $id_group, "ciphered_aes" => $ciphered_aes, "ciphered_nonce" => $ciphered_nonce
            ));
        }
    }
}

// REMOVE FILE
if (isset($_POST["remove_file"])) {

    $deleted = 0;
    $path = $_POST["path"];
    $id_group = $_POST["id_group"];

    $permission = (find("group_user", array("id_user" => $_SESSION["id_user"], "id_group" => $id_group), 1))["id_permission"];

    if ($permission == 1) {
        array_push($errors, "You do not have the authorization!");
        echo 403;
        goto end;
    }

    $folder_list = glob("./groups/$id_group/*", GLOB_ONLYDIR);

    for ($i = 0; $i < count($folder_list); $i++) {
        if (file_exists("./" . $folder_list[$i] . "/$path")) {
            $deleted = unlink($folder_list[$i] . "/$path");
        }
    }

    if ($deleted == 0) {
        array_push($errors, "File not found");
        echo 401;
        goto end;
    } else {
        delete("files", array("path" => $path, "id_group" => $id_group));
        delete("ciphered_for", array("path" => $path, "id_group" => $id_group));
    }
}

// RENAME FILE
if (isset($_POST["rename_file"])) {
    $id_group = $_POST["id_group"];
    $old_filename = $_POST["old_file_name"];
    $new_filename = $_POST["new_file_name"];

    $permission = (find("group_user", array("id_user" => $_SESSION["id_user"], "id_group" => $id_group), 1))["id_permission"];
    if ($permission == 1) {
        array_push($errors, "You do not have the authorization!");
        echo 504;
        goto end;
    }

    if (strstr($new_filename, '/') || strstr($new_filename, '\\') || strstr($new_filename, '*')) {
        echo 503;
        array_push($errors, "Character unallowed in filename");
        goto end;
    }

    $file = find("files", array("id_group" => $id_group, "path" => $old_filename), 1);
    if (!$file) {
        array_push($errors, "File does not exist");
        echo 501;
        goto end;
    }

    $file = find("files", array("id_group" => $id_group, "path" => $new_filename), 1);
    if ($file) {
        array_push($errors, "File name is already used");
        echo 502;
        goto end;
    }

    if (count($errors) == 0) {
        $users = find("group_user", array("id_group" => $id_group));
        foreach ($users as $user) {
            if (file_exists("./groups/$id_group/" . $user["id_user"] . "/$old_filename")) {
                rename("./groups/$id_group/" . $user["id_user"] . "/$old_filename", "./groups/$id_group/" . $user["id_user"] . "/$new_filename");
            }
        }

        $new_date = date("Y-m-d H:i:s");
        update("files", array("path" => $new_filename, "modification_date" => $new_date), array("path" => $old_filename, "id_group" => $id_group));
        update("ciphered_for", array("path" => $new_filename), array("path" => $old_filename, "id_group" => $id_group));
    }
}

// RETRIEVE FILE
if (isset($_POST["retrieve_file"])) {
    $id_group = $_POST["id_group"];
    $path = $_POST["filepath"];

    $file = find("ciphered_for", array("id_group" => $id_group, "path" => $path, "id_user" => $_SESSION["id_user"]), 1);

    if (!$file) {
        array_push($errors, "File not found");
        echo 501;
        goto end;
    } else {
        $response = array();
        $response["ciphered_aes"] = $file["ciphered_aes"];
        $response["ciphered_nonce"] = $file["ciphered_nonce"];

        $path = "./groups/$id_group/" . $_SESSION["id_user"] . "/$path";
        // header("Content-disposition: attachment;filename=" . basename($path));

        echo json_encode($response);
        echo " ~~~ ";
        readfile($path);
        goto end;
    }
}

// ADD FOLDER
if (isset($_POST["create_folder"])) {
    if (empty($_POST['folder_path'])) {
        array_push($errors, "Folder name cannot be empty");
        echo 701;
        goto end;
    }

    $folder_path = $_POST["folder_path"];
    $id_group = $_POST["id_group"];

    $users = find("group_user", array("id_group" => $id_group));

    if (file_exists('./groups/' . $id_group . "/" . $_SESSION["id_user"] . "/" . $folder_path)) {
        array_push($errors, "Folder already exists");
        echo 702;
        goto end;
    }

    create("files", array("path" => $folder_path . "/", "id_group" => $id_group, "author" => $_SESSION["id_user"], "size" => 0));

    foreach ($users as $user) {

        // create all directories not present in user
        $temp_path = "";
        foreach (explode("/",  $user["id_user"] . "/" . $folder_path) as $dir) {
            $temp_path .= "/$dir";
            if (!file_exists("./groups/$id_group/" . $temp_path))
                mkdir("./groups/$id_group/" . $temp_path);
        }

        create("ciphered_for", array("path" => $folder_path . "/", "id_group" => $id_group, "id_user" => $user["id_user"]));
    }
}

// RENAME FOLDER
if (isset($_POST["rename_folder"])) {
    if (empty($_POST['new_folder_path']) || empty($_POST['old_folder_path'])) {
        array_push($errors, "Folder name cannot be empty");
        echo 701;
        goto end;
    }

    $new_folder_path = $_POST["new_folder_path"];
    $old_folder_path = $_POST["old_folder_path"];

    $id_group = $_POST["id_group"];

    $users = find("group_user", array("id_group" => $id_group));

    //Si l'ancien dossier existe et que le nouveau n'existe pas
    if (file_exists('./groups/' . $id_group . "/" . $_SESSION["id_user"] . "/" . $old_folder_path) || !file_exists('./groups/' . $group_id . "/" . $_SESSION["id_user"] . "/" . $new_folder_path)) {
        foreach ($users as $user) {
            try {
                rename("./groups/$id_group/" . $user["id_user"] . "/" . $old_folder_path . "/", "./groups/$id_group/" . $user["id_user"] . "/" . $new_folder_path . "/");
            } catch (Exception $e) {
                array_push($errors, "Can't rename folder");
                echo 704;
                goto end;
            }
        }

        update("files", array("path" => $new_folder_path . "/"), array("id_group" => $id_group, "path" => $old_folder_path . "/"));
        update("ciphered_for", array("path" => $new_folder_path . "/"), array("id_group" => $id_group, "path" => $old_folder_path . "/"));
    } else {
        array_push($errors, "Folder doesn't exist");
        echo 703;
        goto end;
    }
}

// REMOVE FOLDER
if (isset($_POST["remove_folder"])) {
    if (empty($_POST['folder_path'])) {
        array_push($errors, "Folder name cannot be empty");
        echo 701;
        goto end;
    }

    $folder_path = $_POST["folder_path"];

    $id_group = $_POST["id_group"];
    $users = find("group_user", array("id_group" => $id_group));

    if (file_exists('./groups/' . $id_group . "/" . $_SESSION["id_user"] . "/" . $folder_path)) {
        foreach ($users as $user) {
            rrmdir("./groups/$id_group/" . $user["id_user"] . "/" . $folder_path);
        }

        special_query("DELETE FROM files WHERE path LIKE '$folder_path/%' AND id_group = $id_group");
        special_query("DELETE FROM ciphered_for WHERE path LIKE '$folder_path/%' AND id_group = $id_group");
    } else {
        array_push($errors, "Folder doesn't exist");
        echo 703;
        goto end;
    }
}

// id_permission : 1 = lecture || 2 = lecture & écriture || 3 = Administrateur
// CREATE GROUP
if (isset($_POST["create_group"])) {
    if (empty($_POST['group_name']))
        array_push($errors, "Group name cannot be empty");

    $group_name = $_POST["group_name"];
    $current_user = find("users", array("id_user" => $_SESSION["id_user"]), 1);

    $new_group = array("name" => $group_name, "owner" => $current_user["id_user"]);
    create("groups", $new_group);

    $id_group = find("groups", $new_group, 1, array("id_group"), "creation_date")["id_group"];
    create("group_user", array("id_user" => $_SESSION["id_user"], "id_group" => $id_group, "id_permission" => 3));

    if (!file_exists("./groups"))
        mkdir("./groups");

    if (!file_exists("./groups/" . $id_group))
        mkdir("./groups/" . $id_group);
}

// REMOVE GROUP
if (isset($_POST["remove_group"])) {
    if (empty($_POST['id_group']))
        array_push($errors, "Group id cannot be empty");

    $id_group = $_POST['id_group'];
    if (find("groups", array("id_group" => $id_group), 1) == null)
        array_push($errors, "Group doesn't exist");

    $current_group = find("groups", array("id_group" => $id_group), 1);

    if ($_SESSION["id_user"] != $current_group["owner"]) {
        array_push($errors, "User is not the owner of the group");
        echo 500;
        goto end;
    }

    $users = find("group_user", array("id_group" => $id_group));
    foreach ($users as $user) {
        rrmdir("./groups/$id_group");
    }
    delete("groups", array("id_group" => $id_group));
}

end:
if (count($errors) > 0)
    echo " ~~~ " . implode(" ", $errors);
