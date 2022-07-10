<?php

require_once "vendor/autoload.php";

use Otp\Otp;
use Otp\GoogleAuthenticator;
use ParagonIE\ConstantTime\Encoding;
use phpseclib3\Crypt\RSA;
use phpseclib3\Crypt\AES;

require_once("cruds.php");

function set_session_value($user)
{
    $_SESSION["username"] = $user["username"];
    $_SESSION["id_user"] = $user["id_user"];
    $_SESSION["friendrequest_code"] = $user["friendrequest_code"];
}

function generate_random_name()
{
    $name = substr(sha1(mt_rand()), 17, 16);
    return $name;
}

function generate_key_pair()
{
    $private = RSA::createKey();
    $public = $private->getPublicKey();

    return array("public" => $public->toString("PKCS1"), "private" => $private->toString("PKCS1"));
}

function encryptData($data, $publicKey)
{
    if (is_string($publicKey))
        $publicKey = RSA::load($publicKey);

    return $publicKey->encrypt($data);
}

function decryptData($data, $privateKey)
{
    if (is_string($privateKey))
        $privateKey = RSA::load($privateKey);

    return $privateKey->decrypt($data);
}

function encryptDataAES($data, $passphrase)
{
    $aes = new AES('ecb');
    $aes->setKey($passphrase);
    return base64_encode($aes->encrypt($data));
}

function decryptDataAES($data, $passphrase)
{
    $aes = new AES('ecb');
    $aes->setKey($passphrase);
    $data = base64_decode($data);
    return $aes->decrypt($data);
}

function generateTOTPCode()
{
    $secret = GoogleAuthenticator::generateRandom();
    $url = GoogleAuthenticator::getQrCodeUrl('totp', 'FileLocker', $secret);
    return array("secret" => $secret, "url" => $url);
}

function isOTPvalid($given_code, $secret)
{
    $otp = new Otp();
    return ($otp->checkTotp(Encoding::base32DecodeUpper($secret), $given_code));
}

// https://stackoverflow.com/questions/3338123/how-do-i-recursively-delete-a-directory-and-its-entire-contents-files-sub-dir
function rrmdir($dir)
{
    if (is_dir($dir)) {
        $objects = scandir($dir);
        foreach ($objects as $object) {
            if ($object != "." && $object != "..") {
                if (is_dir($dir . DIRECTORY_SEPARATOR . $object) && !is_link($dir . "/" . $object))
                    rrmdir($dir . DIRECTORY_SEPARATOR . $object);
                else
                    unlink($dir . DIRECTORY_SEPARATOR . $object);
            }
        }
        rmdir($dir);
    }
}

// RSA TEST
/*
$key_pair = generate_key_pair();
echo $key_pair["public"];
echo decryptData(encryptData("test", (string) $key_pair["public"]), (string) $key_pair["private"]);
echo decryptData(encryptData("test", $key_pair["public"]), $key_pair["private"]);
*/

// AES TEST
/*
echo encryptDataAES("test", "abcd0192843sssss");
echo encryptDataAES("test", "abcd0192843sssss");
echo decryptDataAES(encryptDataAES("test", "abcd0192843sssss"), "abcd0192843sssss");
*/

// RSA && AES TEST
/*
$key_pair = generate_key_pair();
$backup_code = generate_random_name();
$enc = encryptDataAES((string) $key_pair["private"], $backup_code);
// echo $backup_code . "\n";
// echo $enc . "\n";
echo decryptDataAES($enc, $backup_code);
*/

// TOTP TEST
/*
$otp = new Otp();
$secret = generateTOTPCode();
echo $key = $otp->totp(Encoding::base32DecodeUpper($secret));
echo (isOTPvalid($key, $secret) ? " true" : " false");
*/