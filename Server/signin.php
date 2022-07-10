<?php
require_once("./BACKEND/server.php");
?>

<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta http-equiv="X-UA-Compatible" content="ie=edge" />
    <link rel="stylesheet" href="signin.css" />
    <link href="assets/img/favicon.png" rel="icon">
    <title>S'inscrire</title>

    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/5.0.0-alpha1/css/bootstrap.min.css" integrity="sha384-r4NyP46KrjDleawBgD5tp8Y7UzmLA05oM1iAEQ17CSuDqnUK2+k9luXQOfXJCJ4I" crossorigin="anonymous">
</head>

<body>
    <div class="page">
        <header>

        </header>

        <main>
            <div class="flexbox">
                <video autoplay muted loop id="campfire">
                    <source src=".\assets\img\campfire.mp4" type="video/mp4">
                </video>

                <form method="post" class="signin-form" id="tmContactForm">
                    <div class="container">
                        <h1 class="title">S'inscrire</h1>
                        <p class="txt">Remplissez tous les champs pour continuer</p>

                        <?php if (!empty($_SESSION["errors"])) : ?>
                            <div>
                                <?php
                                foreach ($_SESSION["errors"] as $error)
                                    echo "<p class='error'>$error</p>";
                                ?>
                            </div>
                        <?php endif ?>

                        <hr>

                        <label for="username" class="txt"><b>Nom d'utilisateur</b></label><br>
                        <input type="text" class="txt" placeholder="Nom d'utilisateur" name="reg_username" id="username" required />
                        <br>

                        <label for="email" class="txt"><b>Email</b></label><br>
                        <input type="text" class="txt" placeholder="name@gmail.com" name="reg_email" id="email" required>
                        <br>

                        <label for="psw" class="txt"><b>Mot de passe</b></label><br>
                        <input type="password" class="txt" placeholder="Mon mot de passe" name="reg_password_1" id="psw" required>
                        <br>

                        <label for="psw-repeat" class="txt"><b>Répétez le mode de passe</b></label><br>
                        <input type="password" class="txt" placeholder="Mon mot de passe" name="reg_password_2" id="psw-repeat" required>
                        <hr>

                        <p class="txt">En créant votre compte,
                            vous adhérez à nos <a href="#">Conditions d'Utilisation et Politique de Confidentialité</a>.</p>
                        <button type="submit" name="reg_user" class="signinbtn">S'inscrire</button>


                    </div>

                </form>
            </div>


    </div>

</body>

</html>
<?php unset($_SESSION["errors"]); ?>