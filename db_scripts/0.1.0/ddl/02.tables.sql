CREATE TABLE payment_list (
    id integer NOT NULL,
    batch_id character varying NOT NULL,
    request_id character varying NOT NULL,
    request_timestamp timestamp without time zone NOT NULL,
    from_fa character varying,
    to_fa character varying NOT NULL,
    amount character varying NOT NULL,
    currency character varying NOT NULL,
    status character varying(4) NOT NULL,
    file character varying,
    error_code character varying(27),
    error_msg character varying,
    backend_name character varying,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone,
    active boolean NOT NULL
);
