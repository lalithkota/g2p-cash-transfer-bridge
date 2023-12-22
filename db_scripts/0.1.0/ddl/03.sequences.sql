CREATE SEQUENCE payment_list_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE payment_list_id_seq OWNED BY payment_list.id;
