package com.vistance.bo.routeb;

/** Typed fail-closed error for SDK/API details that are not confirmed yet. */
public final class RequiredInputException extends Exception {
    public static final String CODE = "REQUIRED_INPUT";

    public RequiredInputException(String message) {
        super(message);
    }
}
