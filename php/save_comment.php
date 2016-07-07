<?php
/**
 * Created by PhpStorm.
 * User: rkotulla
 * Date: 7/7/16
 * Time: 12:11 PM
 */

if ($_SERVER['REQUEST_METHOD'] == "POST") {
    $comment = "";
    $objname = test_input($_POST['objname']);
    $comment = test_input($_POST['comment']);

    // Now save the new comment into the right file
    $comment_fn = sprintf("%s/comment.txt", $objname);
    file_put_contents($comment_fn, $comment);

    // Redirect the browser to the updated page
    header(sprintf("Location: %s/", $objname));
} else {
    header("Location: ./");
}

function test_input($data) {
    $data = trim($data);
    $data = stripslashes($data);
    $data = htmlspecialchars($data);
    return $data;
}